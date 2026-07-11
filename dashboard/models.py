from django.db import models


class SecuritySettings(models.Model):
    turnstile_enabled = models.BooleanField(default=True, verbose_name='Cloudflare Turnstile enabled')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Security settings'
        verbose_name_plural = 'Security settings'

    def __str__(self):
        return 'Security settings'

    @classmethod
    def get_solo(cls):
        settings, _ = cls.objects.get_or_create(pk=1)
        return settings
