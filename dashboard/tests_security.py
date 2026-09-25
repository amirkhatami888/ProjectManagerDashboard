from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from .models import SecuritySettings


class BruteForceProtectionSettingTests(TestCase):
    def setUp(self):
        settings = SecuritySettings.get_solo()
        settings.brute_force_enabled = False
        settings.turnstile_enabled = False
        settings.save()
        cache.clear()

    def test_disabled_protection_does_not_record_failed_login_attempts(self):
        self.client.post(
            reverse('accounts:login'),
            {'username': 'unknown-user', 'password': 'invalid-password'},
        )

        self.assertIsNone(cache.get('brute_force_ip_attempts:127.0.0.1'))
        self.assertIsNone(cache.get('brute_force_user_attempts:unknown-user'))
