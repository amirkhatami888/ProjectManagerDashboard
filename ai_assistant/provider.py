"""OpenAI-compatible GapGPT provider with optional streaming."""
import json
import logging
import os
import time

import requests
from django.db.models import Sum
from django.utils import timezone

from .models import AIPlatformSettings, AIUsageRecord


logger = logging.getLogger(__name__)


class ProviderError(RuntimeError):
    pass


class GapGPTProvider:
    def __init__(self, *, endpoint=None, model=None, api_key=None, timeout=None):
        config = AIPlatformSettings.get_solo()
        self.endpoint = self._normalize_endpoint(
            endpoint or config.provider_endpoint or os.getenv("GAPGPT_API_URL", "")
        )
        self.model = self._normalize_model(
            model or config.provider_model or os.getenv("GAPGPT_MODEL", "default")
        )
        self.api_key = api_key or config.get_gapgpt_api_key() or os.getenv("GAPGPT_API_KEY", "")
        self.timeout = timeout or config.request_timeout_seconds
        if not self.endpoint or not self.api_key:
            raise ProviderError("تنظیمات اتصال GapGPT کامل نیست.")

    @staticmethod
    def _normalize_endpoint(endpoint):
        """Accept either a chat-completions URL or an OpenAI-compatible /v1 base."""
        endpoint = str(endpoint or "").strip().rstrip("/")
        if endpoint.endswith("/v1"):
            return f"{endpoint}/chat/completions"
        return endpoint

    @staticmethod
    def _normalize_model(model):
        """Remove quote characters accidentally copied into the model setting."""
        model = str(model or "").strip()
        if len(model) >= 2 and model[0] == model[-1] and model[0] in {"'", '"'}:
            model = model[1:-1].strip()
        return model or "default"

    def _payload(self, messages, tools=None):
        payload = {"model": self.model, "messages": messages, "temperature": 0.2}
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        return payload

    def _check_platform_quota(self):
        config = AIPlatformSettings.get_solo()
        today = timezone.localdate()
        usage = AIUsageRecord.objects.filter(
            provider="gapgpt", created_at__date=today
        ).aggregate(total=Sum("request_count"))["total"] or 0
        month_usage = AIUsageRecord.objects.filter(
            provider="gapgpt",
            created_at__year=today.year,
            created_at__month=today.month,
        ).aggregate(total=Sum("request_count"))["total"] or 0
        if usage >= config.daily_request_limit:
            raise ProviderError("سقف درخواست روزانه سرویس هوش مصنوعی تکمیل شده است.")
        if month_usage >= config.monthly_request_limit:
            raise ProviderError("سقف درخواست ماهانه سرویس هوش مصنوعی تکمیل شده است.")

    def complete(self, messages, tools=None, user=None):
        self._check_platform_quota()
        started = time.monotonic()
        try:
            request_kwargs = {
                "json": self._payload(messages, tools),
                "timeout": self.timeout,
                "headers": {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            }
            response = None
            # Gateways occasionally return a transient 502/503/504. Retry only
            # those statuses so a malformed request is not submitted repeatedly.
            for attempt in range(3):
                response = requests.post(self.endpoint, **request_kwargs)
                if response.status_code not in {502, 503, 504} or attempt == 2:
                    break
                time.sleep(0.5 * (attempt + 1))

            try:
                response.raise_for_status()
            except requests.HTTPError as exc:
                body = " ".join((response.text or "").split())[:500]
                logger.error(
                    "GapGPT request failed: status=%s endpoint=%s model=%s body=%s",
                    response.status_code, self.endpoint, self.model, body,
                )
                if response.status_code in {502, 503, 504}:
                    message = "سرویس هوش مصنوعی موقتاً در دسترس نیست. لطفاً چند لحظه بعد دوباره تلاش کنید."
                elif response.status_code in {401, 403}:
                    message = "کلید دسترسی سرویس هوش مصنوعی معتبر نیست یا اجازه استفاده ندارد."
                elif response.status_code == 404:
                    message = "نشانی یا مدل سرویس هوش مصنوعی پیدا نشد؛ تنظیمات endpoint و model را بررسی کنید."
                else:
                    message = f"سرویس هوش مصنوعی درخواست را نپذیرفت (کد {response.status_code})."
                raise ProviderError(message) from exc

            data = response.json()
            choice = (data.get("choices") or [{}])[0]
            message = choice.get("message") or {}
            content = message.get("content") or data.get("output") or data.get("answer") or data.get("text")
            tool_calls = message.get("tool_calls") or []
            if content is None and not tool_calls:
                raise ProviderError("پاسخ معتبر از GapGPT دریافت نشد.")
            usage = data.get("usage") or {}
            if user:
                AIUsageRecord.objects.create(
                    user=user, provider="gapgpt",
                    input_tokens=usage.get("prompt_tokens", 0) or 0,
                    output_tokens=usage.get("completion_tokens", 0) or 0,
                    latency_ms=int((time.monotonic() - started) * 1000),
                )
            return {"content": str(content or ""), "message": message, "raw": data,
                    "usage": usage}
        except requests.RequestException as exc:
            logger.error(
                "GapGPT connection failed: endpoint=%s model=%s error=%s",
                self.endpoint, self.model, type(exc).__name__,
            )
            if user:
                AIUsageRecord.objects.create(user=user, provider="gapgpt",
                                             status="error", error_code=type(exc).__name__,
                                             latency_ms=int((time.monotonic() - started) * 1000))
            raise ProviderError(
                "ارتباط با سرویس هوش مصنوعی برقرار نشد؛ اتصال اینترنت سرور و endpoint را بررسی کنید."
            ) from exc
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            logger.error(
                "GapGPT returned invalid JSON: endpoint=%s model=%s error=%s",
                self.endpoint, self.model, type(exc).__name__,
            )
            if user:
                AIUsageRecord.objects.create(user=user, provider="gapgpt",
                                             status="error", error_code=type(exc).__name__,
                                             latency_ms=int((time.monotonic() - started) * 1000))
            raise ProviderError("پاسخ سرویس هوش مصنوعی قابل پردازش نیست.") from exc

    def stream(self, messages, tools=None):
        """Yield text chunks for providers implementing SSE/OpenAI streaming."""
        response = requests.post(
            self.endpoint, json={**self._payload(messages, tools), "stream": True},
            timeout=self.timeout, stream=True,
            headers={"Authorization": f"Bearer {self.api_key}",
                     "Content-Type": "application/json"},
        )
        response.raise_for_status()
        for line in response.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                break
            try:
                chunk = json.loads(data)
            except json.JSONDecodeError:
                continue
            delta = ((chunk.get("choices") or [{}])[0].get("delta") or {})
            if delta.get("content"):
                yield delta["content"]
