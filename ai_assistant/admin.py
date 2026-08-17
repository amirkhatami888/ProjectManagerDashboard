from django.contrib import admin

from .models import (
    AIAuditLog, AIConversation, AIMessage, AIPendingAction, AIPlatformSettings,
    AIRolePolicy, AIUsageRecord, AIUserPolicy,
)
from .forms import AIPlatformSettingsForm


@admin.register(AIPlatformSettings)
class AIPlatformSettingsAdmin(admin.ModelAdmin):
    form = AIPlatformSettingsForm
    list_display = ("provider_name", "provider_model", "enabled", "updated_at")
    readonly_fields = ("gapgpt_api_key_encrypted", "tavily_api_key_encrypted", "updated_at")


@admin.register(AIUserPolicy)
class AIUserPolicyAdmin(admin.ModelAdmin):
    list_display = ("user", "is_enabled", "daily_message_limit", "monthly_message_limit",
                    "allow_web_search", "allow_write_actions", "updated_at")
    list_filter = ("is_enabled", "allow_web_search", "allow_write_actions")
    search_fields = ("user__username", "user__email")
    raw_id_fields = ("user",)
    readonly_fields = ("api_key_encrypted", "updated_at")


@admin.register(AIRolePolicy)
class AIRolePolicyAdmin(admin.ModelAdmin):
    list_display = ("role", "is_enabled", "allow_web_search", "allow_write_actions")
    list_filter = ("is_enabled", "allow_web_search", "allow_write_actions")


@admin.register(AIConversation)
class AIConversationAdmin(admin.ModelAdmin):
    list_display = ("user", "title", "context_type", "updated_at")
    search_fields = ("user__username", "title")
    readonly_fields = ("created_at", "updated_at")


@admin.register(AIAuditLog)
class AIAuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "user", "action", "status")
    list_filter = ("status", "action")
    search_fields = ("user__username", "action")
    readonly_fields = ("created_at",)


@admin.register(AIMessage)
class AIMessageAdmin(admin.ModelAdmin):
    list_display = ("created_at", "conversation", "role")
    list_filter = ("role",)
    readonly_fields = ("created_at",)


@admin.register(AIPendingAction)
class AIPendingActionAdmin(admin.ModelAdmin):
    list_display = ("created_at", "user", "action_type", "status", "expires_at", "confirmed_at")
    list_filter = ("action_type", "status")
    search_fields = ("user__username", "user__email")
    readonly_fields = ("created_at", "confirmed_at")


@admin.register(AIUsageRecord)
class AIUsageRecordAdmin(admin.ModelAdmin):
    list_display = ("created_at", "user", "provider", "status", "input_tokens",
                    "output_tokens", "latency_ms")
    list_filter = ("provider", "status")
    readonly_fields = ("created_at",)
