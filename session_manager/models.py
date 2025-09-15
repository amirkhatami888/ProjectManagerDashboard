from django.db import models
from django.contrib.auth.models import User


class SessionLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'session_manager_sessionlog'
        ordering = ['-last_activity']

    def __str__(self):
        return f"{self.user.username} - {self.session_key[:8]}..."


class SessionSecurity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    failed_attempts = models.IntegerField(default=0)
    last_failed_attempt = models.DateTimeField(null=True, blank=True)
    is_locked = models.BooleanField(default=False)
    lockout_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'session_manager_sessionsecurity'

    def __str__(self):
        return f"{self.user.username} - Security"
