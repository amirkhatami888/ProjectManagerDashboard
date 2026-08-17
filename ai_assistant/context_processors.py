from .models import AIPlatformSettings, AIUserPolicy, AIRolePolicy


def availability(request):
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return {"ai_policy_enabled": False, "ai_web_search_enabled": False}
    platform = AIPlatformSettings.objects.filter(pk=1).only("enabled").first()
    if platform and not platform.enabled:
        return {"ai_policy_enabled": False, "ai_web_search_enabled": False}
    policy = AIUserPolicy.objects.filter(user=request.user).only("is_enabled").first()
    # Users without a policy receive the default policy on first use.
    role = AIRolePolicy.objects.filter(role=getattr(request.user, "role", "")).only(
        "is_enabled", "allow_web_search"
    ).first()
    web_enabled = (policy is None or policy.allow_web_search) and (
        role is None or role.allow_web_search
    )
    return {
        "ai_policy_enabled": (
            (policy is None or policy.is_enabled)
            and (role is None or role.is_enabled)
        ),
        "ai_web_search_enabled": web_enabled,
    }
