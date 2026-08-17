import json
import re

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods

from .models import AIUserPolicy, AIRolePolicy, AIConversation, AIMessage, AIAuditLog
from .orchestration import run_tool_loop
from .provider import GapGPTProvider, ProviderError
from .services import make_messages
from .tools import explain_field, preview_update, confirm_update


def _asks_for_web(query):
    """Detect explicit requests for current Internet/web information."""
    text = (query or "").lower()
    markers = (
        "از روی اینترنت", "اینترنت", "جستجوی وب", "روی وب", "منبع وب",
        "internet", "web search", "online", "search the web",
    )
    return any(marker in text for marker in markers)


def get_policy(user):
    policy, _ = AIUserPolicy.objects.get_or_create(user=user)
    return policy


def effective_policy(user):
    """Return the effective policy without mutating the stored user policy."""
    policy = get_policy(user)
    if getattr(user, "role", None) == "CEO":
        # CEO access is intentionally independent of persisted user/role limits.
        policy.is_enabled = True
        policy.allow_web_search = True
        policy.allow_write_actions = True
        return policy

    role = AIRolePolicy.objects.filter(role=getattr(user, "role", "")).first()
    if not role:
        return policy
    # Role restrictions are a hard ceiling. Keep the persisted user policy
    # unchanged so re-enabling a role restores each user's prior settings.
    policy.is_enabled = policy.is_enabled and role.is_enabled
    policy.allow_web_search = policy.allow_web_search and role.allow_web_search
    policy.allow_write_actions = policy.allow_write_actions and role.allow_write_actions
    policy.daily_message_limit = min(policy.daily_message_limit, role.daily_message_limit)
    policy.monthly_message_limit = min(policy.monthly_message_limit, role.monthly_message_limit)
    return policy


def _extract_agent_directives(answer):
    """Remove machine directives from visible text and return validated payloads."""
    options = []
    action = None
    option_match = re.search(r"<options>([\s\S]*?)</options>", answer)
    if option_match:
        try:
            parsed = json.loads(option_match.group(1))
            if isinstance(parsed, list):
                options = [str(item)[:160] for item in parsed[:6] if str(item).strip()]
        except (TypeError, ValueError):
            pass
        answer = answer.replace(option_match.group(0), "").strip()
    action_match = re.search(r"<action>([\s\S]*?)</action>", answer)
    if action_match:
        try:
            parsed = json.loads(action_match.group(1))
            if isinstance(parsed, dict) and parsed.get("type") == "update_field":
                action = parsed
        except (TypeError, ValueError):
            pass
        answer = answer.replace(action_match.group(0), "").strip()
    return answer, options, action


@login_required
def assistant_panel(request):
    return render(request, "ai_assistant/panel.html", {"ai_policy": effective_policy(request.user)})


@login_required
@require_http_methods(["POST"])
def assistant_chat(request):
    policy = effective_policy(request.user)
    if not policy.can_use():
        return JsonResponse({"ok": False, "error": "دستیار برای شما غیرفعال است یا سقف مصرف مجاز به پایان رسیده است."}, status=403)
    try:
        payload = json.loads(request.body or "{}")
        query = str(payload.get("message", "")).strip()
        if not query:
            return JsonResponse({"ok": False, "error": "پیام خالی است."}, status=400)
        conversation_id = payload.get("conversation_id")
        conversation = None
        if conversation_id:
            conversation = AIConversation.objects.filter(pk=conversation_id, user=request.user).first()
        if conversation is None:
            context_type = str(payload.get("context_type", ""))[:30]
            try:
                context_id = int(payload["context_id"]) if payload.get("context_id") else None
            except (TypeError, ValueError):
                context_id = None
            conversation = AIConversation.objects.create(user=request.user,
                title=query[:200], context_type=context_type, context_id=context_id)

        history = [{"role": m.role, "content": m.content}
                   for m in conversation.messages.filter(role__in=["user", "assistant"]).order_by("created_at")]
        # Explicit wording such as «از روی اینترنت بگو» should not depend on
        # a hidden checkbox, especially in the admin/CEO quick panel.
        use_web = (bool(payload.get("use_web")) or _asks_for_web(query)) and policy.allow_web_search
        use_local_js = bool(payload.get("use_local_js")) and bool(
            getattr(request.user, "is_staff", False)
        )
        messages = make_messages(history, query, conversation.context_type, conversation.context_id)
        provider = GapGPTProvider(
            api_key=policy.get_api_key() or None,
            model=policy.model_name or None,
        )
        result = run_tool_loop(
            request.user, messages, provider,
            allow_web_search=use_web, allow_local_js=use_local_js, max_rounds=5,
        )
        answer, options, requested_action = _extract_agent_directives(result["content"])
        action = None
        if requested_action:
            try:
                if policy.allow_write_actions:
                    action = preview_update(
                        request.user,
                        requested_action["entity"],
                        requested_action["id"],
                        requested_action["field"],
                        requested_action["value"],
                    )
                    answer += "\n\nبرای اجرای تغییر، پیش‌نمایش زیر را بررسی و تأیید کنید."
                else:
                    answer += "\n\nعملیات تغییردهنده برای حساب شما فعال نیست. مدیر سامانه می‌تواند آن را از پنل AI فعال کند."
            except (KeyError, TypeError, ValueError, PermissionError) as exc:
                answer += f"\n\nامکان آماده‌سازی این تغییر وجود ندارد: {exc}"
        AIMessage.objects.create(conversation=conversation, role="user", content=query)
        AIMessage.objects.create(conversation=conversation, role="assistant", content=answer,
                                 metadata={"web_search": use_web, "local_js": use_local_js,
                                           "tools": result["trace"],
                                           "options": options})
        AIAuditLog.objects.create(
            user=request.user, action="chat",
            details={"web_search": use_web, "local_js": use_local_js, "tools": result["trace"],
                     "conversation_id": conversation.pk},
        )
        return JsonResponse({"ok": True, "answer": answer, "action": action,
                             "options": options,
                             "conversation_id": conversation.pk,
                             "usage_today": get_policy(request.user).messages_today()})
    except ProviderError as exc:
        AIAuditLog.objects.create(user=request.user, action="chat", status="error",
                                  details={"error": str(exc)[:500]})
        return JsonResponse({"ok": False, "error": str(exc)}, status=502)
    except Exception as exc:
        AIAuditLog.objects.create(user=request.user, action="chat", status="error",
                                  details={"error": str(exc)[:500]})
        return JsonResponse({
            "ok": False,
            "error": "در پردازش درخواست خطایی رخ داد. شناسه رویداد در گزارش مدیریتی ثبت شد.",
        }, status=500)


@login_required
@require_http_methods(["GET"])
def conversation_messages(request, pk):
    conversation = get_object_or_404(AIConversation, pk=pk, user=request.user)
    return JsonResponse({"messages": list(conversation.messages.values("role", "content", "created_at"))})


@login_required
@require_http_methods(["GET"])
def field_help(request):
    result = explain_field(request.GET.get("entity", ""), request.GET.get("field", ""))
    if not result:
        return JsonResponse({"ok": False, "error": "راهنمای این فیلد پیدا نشد."}, status=404)
    return JsonResponse({"ok": True, "field": result})


@login_required
@require_http_methods(["POST"])
def confirm_action(request):
    policy = effective_policy(request.user)
    if not policy.allow_write_actions:
        return JsonResponse({"ok": False, "error": "عملیات تغییردهنده برای حساب شما فعال نیست."}, status=403)
    try:
        data = json.loads(request.body or "{}")
        result = confirm_update(request.user, int(data["action_id"]))
        AIAuditLog.objects.create(user=request.user, action="confirm_update",
                                  details=result)
        return JsonResponse({"ok": True, "message": f"فیلد «{result['field_label']}» با موفقیت به‌روزرسانی شد.",
                             "action": result})
    except Exception as exc:
        AIAuditLog.objects.create(user=request.user, action="confirm_update",
                                  status="error", details={"error": str(exc)[:500]})
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)
