from django.conf import settings
from django.db import models
from django.utils import timezone


class AIUserPolicy(models.Model):
    """Per-user AI entitlement and safety controls."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name="ai_policy", verbose_name="کاربر")
    is_enabled = models.BooleanField(default=True, verbose_name="فعال")
    daily_message_limit = models.PositiveIntegerField(default=30, verbose_name="سقف پیام روزانه")
    monthly_message_limit = models.PositiveIntegerField(default=500, verbose_name="سقف پیام ماهانه")
    allow_web_search = models.BooleanField(default=True, verbose_name="اجازه جستجوی وب")
    allow_write_actions = models.BooleanField(default=False, verbose_name="اجازه عملیات تغییردهنده")
    api_key = models.CharField(max_length=500, blank=True, default="", verbose_name="کلید API اختصاصی")
    api_key_encrypted = models.TextField(blank=True, default="", editable=False)
    model_name = models.CharField(max_length=100, blank=True, default="", verbose_name="مدل")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "سیاست دستیار کاربر"
        verbose_name_plural = "سیاست‌های دستیار کاربران"

    def __str__(self):
        return f"{self.user} - {'فعال' if self.is_enabled else 'غیرفعال'}"

    def messages_today(self):
        return AIMessage.objects.filter(
            conversation__user=self.user,
            role="user",
            created_at__date=timezone.localdate(),
        ).count()

    def messages_this_month(self):
        today = timezone.localdate()
        return AIMessage.objects.filter(
            conversation__user=self.user,
            role="user",
            created_at__year=today.year,
            created_at__month=today.month,
        ).count()

    def can_use(self):
        platform = AIPlatformSettings.objects.filter(pk=1).first()
        if platform and not platform.enabled:
            return False
        return (
            self.is_enabled
            and self.messages_today() < self.daily_message_limit
            and self.messages_this_month() < self.monthly_message_limit
        )

    def get_api_key(self):
        """Return the legacy key or the encrypted key, decrypted in application memory."""
        if self.api_key_encrypted:
            from .security import decrypt_secret
            return decrypt_secret(self.api_key_encrypted)
        return self.api_key

    def save(self, *args, **kwargs):
        # The visible field is write-only: setting it also rotates an existing key.
        if self.api_key:
            from .security import encrypt_secret
            self.api_key_encrypted = encrypt_secret(self.api_key)
            self.api_key = ""
        super().save(*args, **kwargs)


class AIConversation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="ai_conversations", verbose_name="کاربر")
    title = models.CharField(max_length=200, default="گفتگوی جدید", verbose_name="عنوان")
    context_type = models.CharField(max_length=30, blank=True, default="")
    context_id = models.PositiveBigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "گفتگوی دستیار"
        verbose_name_plural = "گفتگوهای دستیار"
        ordering = ["-updated_at"]


class AIMessage(models.Model):
    ROLE_CHOICES = [("user", "کاربر"), ("assistant", "دستیار"), ("tool", "ابزار")]
    conversation = models.ForeignKey(AIConversation, on_delete=models.CASCADE,
                                     related_name="messages", verbose_name="گفتگو")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "پیام دستیار"
        verbose_name_plural = "پیام‌های دستیار"
        ordering = ["created_at"]


class AIAuditLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                             null=True, related_name="ai_audit_logs")
    action = models.CharField(max_length=100)
    status = models.CharField(max_length=30, default="success")
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "گزارش امنیتی دستیار"
        verbose_name_plural = "گزارش‌های امنیتی دستیار"
        ordering = ["-created_at"]


class AIPendingAction(models.Model):
    """A validated write operation waiting for explicit user confirmation."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="ai_pending_actions", verbose_name="کاربر")
    action_type = models.CharField(max_length=40, default="update_field")
    payload = models.JSONField(default=dict)
    status = models.CharField(max_length=20, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "عملیات در انتظار تأیید AI"
        verbose_name_plural = "عملیات در انتظار تأیید AI"
        ordering = ["-created_at"]


class AIPlatformSettings(models.Model):
    """Singleton global AI configuration; secrets are encrypted at rest."""

    enabled = models.BooleanField(default=True, verbose_name="فعال")
    provider_name = models.CharField(max_length=50, default="gapgpt")
    provider_endpoint = models.URLField(blank=True, default="")
    provider_model = models.CharField(max_length=120, default="default")
    gapgpt_api_key_encrypted = models.TextField(blank=True, default="", editable=False)
    tavily_api_key_encrypted = models.TextField(blank=True, default="", editable=False)
    request_timeout_seconds = models.PositiveIntegerField(default=60)
    daily_request_limit = models.PositiveIntegerField(default=1000)
    monthly_request_limit = models.PositiveIntegerField(default=20000)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "تنظیمات سراسری دستیار"
        verbose_name_plural = "تنظیمات سراسری دستیار"

    def __str__(self):
        return "تنظیمات سراسری دستیار"

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def get_gapgpt_api_key(self):
        from .security import decrypt_secret
        return decrypt_secret(self.gapgpt_api_key_encrypted)

    def get_tavily_api_key(self):
        from .security import decrypt_secret
        return decrypt_secret(self.tavily_api_key_encrypted)


class AIRolePolicy(models.Model):
    """Role-level defaults, overridden by a user's AIUserPolicy."""

    role = models.CharField(max_length=30, unique=True)
    is_enabled = models.BooleanField(default=True)
    daily_message_limit = models.PositiveIntegerField(default=30)
    monthly_message_limit = models.PositiveIntegerField(default=500)
    allow_web_search = models.BooleanField(default=True)
    allow_write_actions = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "سیاست نقش دستیار"
        verbose_name_plural = "سیاست‌های نقش دستیار"


class AIUsageRecord(models.Model):
    """Auditable provider/search usage, without storing prompts or secrets."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                             null=True, related_name="ai_usage_records")
    provider = models.CharField(max_length=50)
    request_count = models.PositiveIntegerField(default=1)
    input_tokens = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)
    search_credits = models.PositiveIntegerField(default=0)
    latency_ms = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, default="success")
    error_code = models.CharField(max_length=100, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "مصرف دستیار"
        verbose_name_plural = "مصرف دستیار"
        ordering = ["-created_at"]
