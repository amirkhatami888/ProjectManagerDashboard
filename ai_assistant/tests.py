from django.test import TestCase
from django.urls import reverse
from accounts.models import User
from creator_program.models import Program
from unittest.mock import Mock, patch
import requests

from .orchestration import run_tool_loop
from .tools import preview_update
from .views import _extract_agent_directives, effective_policy
from .models import AIPlatformSettings, AIUserPolicy, AIRolePolicy
from .provider import GapGPTProvider, ProviderError
from .search import tavily_search
from .js_runner import run_local_js
import tempfile
from pathlib import Path


class AIAssistantTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="ai-test", email="ai-test@example.com", password="test-pass-123"
        )

    def test_policy_limits_usage(self):
        policy = AIUserPolicy.objects.create(user=self.user, daily_message_limit=0)
        self.assertFalse(policy.can_use())

    def test_ceo_has_unlimited_full_access(self):
        self.user.role = "CEO"
        self.user.save(update_fields=["role"])
        AIUserPolicy.objects.create(
            user=self.user,
            is_enabled=False,
            daily_message_limit=0,
            monthly_message_limit=0,
            allow_web_search=False,
            allow_write_actions=False,
        )
        AIRolePolicy.objects.create(
            role="CEO",
            is_enabled=False,
            daily_message_limit=0,
            monthly_message_limit=0,
            allow_web_search=False,
            allow_write_actions=False,
        )

        policy = effective_policy(self.user)

        self.assertTrue(policy.is_enabled)
        self.assertTrue(policy.allow_web_search)
        self.assertTrue(policy.allow_write_actions)
        self.assertTrue(policy.can_use())

    def test_explicit_internet_request_enables_web_search(self):
        from .views import _asks_for_web
        self.assertTrue(_asks_for_web("از روی اینترنت بگو ساختمان صلح کجاست"))
        self.assertFalse(_asks_for_web("پیشرفت پروژه را بگو"))

    def test_panel_requires_login(self):
        response = self.client.get(reverse("ai_assistant:panel"))
        self.assertEqual(response.status_code, 302)

    def test_role_policy_disables_assistant(self):
        self.user.role = "EXPERT"
        self.user.save(update_fields=["role"])
        AIRolePolicy.objects.create(role="EXPERT", is_enabled=False)
        self.client.force_login(self.user)

        response = self.client.get(reverse("ai_assistant:panel"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "دستیار هوشمند برای نقش یا حساب کاربری شما غیرفعال است")

    def test_admin_can_update_role_policy_from_control_center(self):
        admin = User.objects.create_superuser(
            username="ai-admin", email="ai-admin@example.com", password="test-pass-123"
        )
        self.client.force_login(admin)
        response = self.client.post(reverse("dashboard:ai_control_action"), {
            "action": "save_role_policy",
            "role": "PROVINCE_MANAGER",
            "daily_message_limit": 30,
            "monthly_message_limit": 500,
        })
        self.assertRedirects(response, reverse("dashboard:ai_control_center"))
        self.assertFalse(AIRolePolicy.objects.get(role="PROVINCE_MANAGER").is_enabled)

    def test_province_manager_role_policy_disables_assistant(self):
        self.user.role = "PROVINCE_MANAGER"
        self.user.save(update_fields=["role"])
        AIRolePolicy.objects.create(role="PROVINCE_MANAGER", is_enabled=False)
        self.client.force_login(self.user)

        panel = self.client.get(reverse("ai_assistant:panel"))
        self.assertContains(panel, "دستیار هوشمند برای نقش یا حساب کاربری شما غیرفعال است")

        response = self.client.post(
            reverse("ai_assistant:chat"),
            data='{"message":"سلام"}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(response.json()["ok"])

    def test_role_reenable_preserves_user_policy(self):
        self.user.role = "PROVINCE_MANAGER"
        self.user.save(update_fields=["role"])
        user_policy = AIUserPolicy.objects.create(user=self.user, is_enabled=True)
        role_policy = AIRolePolicy.objects.create(role="PROVINCE_MANAGER", is_enabled=False)
        self.client.force_login(self.user)

        self.assertFalse(self.client.get(reverse("ai_assistant:panel")).context["ai_policy"].is_enabled)
        role_policy.is_enabled = True
        role_policy.save(update_fields=["is_enabled", "updated_at"])

        self.assertTrue(self.client.get(reverse("ai_assistant:panel")).context["ai_policy"].is_enabled)
        self.assertTrue(AIUserPolicy.objects.get(pk=user_policy.pk).is_enabled)

    def test_agent_directives_are_removed_from_visible_answer(self):
        answer, options, action = _extract_agent_directives(
            'کدام پروژه؟ <options>["پروژه الف","پروژه ب"]</options>'
            '<action>{"type":"update_field","entity":"project","id":2,'
            '"field":"name","value":"نام جدید"}</action>'
        )
        self.assertEqual(answer, "کدام پروژه؟")
        self.assertEqual(options, ["پروژه الف", "پروژه ب"])
        self.assertEqual(action["field"], "name")

    def test_tool_loop_executes_allowlisted_tool_then_returns_answer(self):
        provider = Mock()
        provider.complete.side_effect = [
            {
                "content": "",
                "message": {"role": "assistant", "content": None, "tool_calls": [{
                    "id": "call-1", "function": {
                        "name": "explain_field",
                        "arguments": '{"entity":"project","field":"name"}',
                    },
                }]},
                "usage": {},
            },
            {
                "content": "نام پروژه برای شناسایی پروژه استفاده می‌شود.",
                "message": {"role": "assistant",
                            "content": "نام پروژه برای شناسایی پروژه استفاده می‌شود."},
                "usage": {},
            },
        ]
        result = run_tool_loop(
            self.user, [{"role": "user", "content": "نام پروژه چیست؟"}],
            provider, allow_web_search=False,
        )
        self.assertIn("شناسایی پروژه", result["content"])
        self.assertEqual(result["trace"], [{"tool": "explain_field", "ok": True}])
        self.assertEqual(provider.complete.call_count, 2)

    def test_tool_loop_responds_to_all_tool_calls_when_execution_is_limited(self):
        calls = [
            {"id": f"call-{index}", "function": {
                "name": "explain_field",
                "arguments": '{"entity":"project","field":"name"}',
            }}
            for index in range(7)
        ]
        provider = Mock()
        provider.complete.side_effect = [
            {
                "content": "",
                "message": {"role": "assistant", "content": None, "tool_calls": calls},
                "usage": {},
            },
            {
                "content": "پاسخ نهایی",
                "message": {"role": "assistant", "content": "پاسخ نهایی"},
                "usage": {},
            },
        ]

        result = run_tool_loop(
            self.user, [{"role": "user", "content": "توضیح بده"}],
            provider, allow_web_search=False,
        )

        sent_messages = provider.complete.call_args_list[1].args[0]
        tool_messages = [message for message in sent_messages if message["role"] == "tool"]
        self.assertEqual(len(tool_messages), 7)
        self.assertEqual(
            {message["tool_call_id"] for message in tool_messages},
            {f"call-{index}" for index in range(7)},
        )
        self.assertEqual(result["trace"][-1], {
            "tool": "explain_field", "ok": False, "error": "tool_limit",
        })

    def test_tool_loop_uses_tool_free_fallback_after_round_limit(self):
        provider = Mock()
        repeated_tool_response = {
            "content": "",
            "message": {"role": "assistant", "content": None, "tool_calls": [{
                "id": "call-1",
                "function": {
                    "name": "explain_field",
                    "arguments": '{"entity":"project","field":"name"}',
                },
            }]},
            "usage": {},
        }
        provider.complete.side_effect = [
            repeated_tool_response,
            {"content": "پاسخ نهایی بدون ابزار", "message": {
                "role": "assistant", "content": "پاسخ نهایی بدون ابزار",
            }, "usage": {}},
        ]

        result = run_tool_loop(
            self.user, [{"role": "user", "content": "توضیح بده"}],
            provider, allow_web_search=False, max_rounds=1,
        )

        self.assertEqual(result["content"], "پاسخ نهایی بدون ابزار")
        self.assertEqual(provider.complete.call_args_list[1].kwargs["tools"], [])
        self.assertEqual(result["trace"][-1]["error"], "tool_round_limit")

    def test_expert_cannot_prepare_update_for_someone_elses_program(self):
        owner = User.objects.create_user(
            username="owner", email="owner@example.com", password="test-pass-123"
        )
        program = Program.objects.create(
            title="طرح آزمایشی", program_type="پایگاه امداد جادهای",
            province="تهران", city="تهران", license_state="دارد",
            license_code="L-1", created_by=owner,
        )
        self.user.role = "EXPERT"
        self.user.province = "تهران"
        self.user.save(update_fields=["role", "province"])
        with self.assertRaises(PermissionError):
            preview_update(self.user, "program", program.pk, "title", "عنوان جدید")

    def test_user_api_key_can_be_rotated_without_plaintext_storage(self):
        policy = AIUserPolicy.objects.create(user=self.user, api_key="first-secret")
        first_encrypted = policy.api_key_encrypted
        policy.api_key = "second-secret"
        policy.save()
        policy.refresh_from_db()
        self.assertEqual(policy.api_key, "")
        self.assertNotEqual(policy.api_key_encrypted, first_encrypted)
        self.assertEqual(policy.get_api_key(), "second-secret")

    @patch("ai_assistant.provider.time.sleep")
    @patch("ai_assistant.provider.requests.post")
    def test_provider_retries_transient_gateway_errors(self, post, sleep):
        AIPlatformSettings.objects.create(
            provider_endpoint="https://api.example.test/v1",
            provider_model="test-model",
            request_timeout_seconds=5,
        )
        first = Mock(status_code=502, text="temporary gateway failure")
        second = Mock(status_code=200)
        second.json.return_value = {
            "choices": [{"message": {"role": "assistant", "content": "سلام"}}],
            "usage": {},
        }
        post.side_effect = [first, second]

        result = GapGPTProvider(api_key="test-key").complete(
            [{"role": "user", "content": "سلام"}], user=self.user
        )

        self.assertEqual(result["content"], "سلام")
        self.assertEqual(post.call_count, 2)
        sleep.assert_called_once_with(0.5)

    @patch("ai_assistant.provider.requests.post")
    def test_provider_reports_authentication_errors(self, post):
        AIPlatformSettings.objects.create(
            provider_endpoint="https://api.example.test/v1",
            provider_model="test-model",
        )
        response = Mock(status_code=401, text="invalid api key")
        response.raise_for_status.side_effect = requests.HTTPError("401")
        post.return_value = response

        with self.assertRaisesMessage(ProviderError, "کلید دسترسی"):
            GapGPTProvider(api_key="test-key").complete(
                [{"role": "user", "content": "سلام"}], user=self.user
            )

    @patch("ai_assistant.search.requests.post")
    def test_web_search_returns_citation_ready_results(self, post):
        AIPlatformSettings.objects.create(
            tavily_api_key_encrypted="",
            request_timeout_seconds=5,
        )
        response = Mock(status_code=200)
        response.json.return_value = {
            "answer": "خلاصه منبع",
            "results": [{
                "title": "منبع رسمی",
                "url": "https://example.gov/rule",
                "content": "متن منبع",
                "score": 0.91,
                "published_date": "2026-08-01",
            }],
        }
        post.return_value = response
        with patch.dict("os.environ", {"TAVILY_API_KEY": "test-key"}):
            result = tavily_search("ضابطه جدید", user=self.user)
        self.assertEqual(result["results"][0]["domain"], "example.gov")
        self.assertEqual(result["results"][0]["source_type"], "government")
        self.assertEqual(result["answer"], "خلاصه منبع")
        self.assertEqual(post.call_args.kwargs["json"]["search_depth"], "advanced")

    @patch("ai_assistant.search.requests.get")
    def test_web_search_uses_no_key_public_fallback(self, get):
        AIPlatformSettings.objects.create(request_timeout_seconds=5)
        response = Mock(status_code=200, text=(
            '<a class="result__a" href="https://example.org/address">ساختمان صلح</a>'
            '<div class="result__snippet">تهران، خیابان ولیعصر</div>'
        ))
        get.return_value = response
        result = tavily_search("ساختمان صلح", user=self.user)
        self.assertEqual(result["results"][0]["title"], "ساختمان صلح")
        self.assertEqual(result["results"][0]["domain"], "example.org")

    @patch("ai_assistant.js_runner.subprocess.run")
    def test_local_js_runner_restricts_path_and_uses_node_without_shell(self, run):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            script = root / "hello.js"
            script.write_text("console.log('ok')", encoding="utf-8")
            completed = Mock(returncode=0, stdout="ok\n", stderr="")
            run.return_value = completed
            with patch.dict("os.environ", {
                "AI_LOCAL_JS_ENABLED": "true",
                "AI_JS_WORKSPACE_ROOT": str(root),
            }):
                result = run_local_js("hello.js", ["one"])
        self.assertTrue(result["ok"])
        self.assertEqual(run.call_args.args[0][3:], [str(script), "one"])
        self.assertFalse(run.call_args.kwargs["shell"])

    def test_local_js_runner_rejects_path_traversal(self):
        with patch.dict("os.environ", {
            "AI_LOCAL_JS_ENABLED": "true",
            "AI_JS_WORKSPACE_ROOT": tempfile.gettempdir(),
        }):
            with self.assertRaises(PermissionError):
                run_local_js("../outside.js")
