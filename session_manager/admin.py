from django.contrib import admin
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User
from django.utils import timezone

class SessionAdmin(admin.ModelAdmin):
    list_display = ('session_key', 'get_user', 'expire_date', 'is_expired')
    list_filter = ('expire_date',)
    search_fields = ('session_key',)
    readonly_fields = ('session_key', 'session_data', 'expire_date')
    
    def get_user(self, obj):
        try:
            session_data = obj.get_decoded()
            if 'user_id' in session_data:
                user = User.objects.get(id=session_data['user_id'])
                return user.username
        except (User.DoesNotExist, KeyError):
            pass
        return 'Anonymous'
    get_user.short_description = 'User'
    
    def is_expired(self, obj):
        return obj.expire_date < timezone.now()
    is_expired.boolean = True
    is_expired.short_description = 'Expired'

# Check if Session is already registered before unregistering
if admin.site.is_registered(Session):
    admin.site.unregister(Session)
admin.site.register(Session, SessionAdmin)