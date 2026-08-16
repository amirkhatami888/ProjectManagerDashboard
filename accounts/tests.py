from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class AccountPageTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='account-page-user',
            email='account-page-user@example.com',
            password='Strong-test-password-123',
        )
        self.client.force_login(self.user)

    def test_profile_page_renders(self):
        response = self.client.get(reverse('accounts:profile'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/profile.html')

    def test_password_change_page_renders(self):
        response = self.client.get(reverse('accounts:password_change'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/password_change.html')
