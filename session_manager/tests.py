from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.test import Client
from django.urls import reverse
import json

class SessionManagerTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()
    
    def test_session_info_authenticated(self):
        """Test session info for authenticated user"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('session_manager:session_info'))
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(data['username'], 'testuser')
        self.assertTrue(data['is_authenticated'])
    
    def test_session_info_unauthenticated(self):
        """Test session info for unauthenticated user"""
        response = self.client.get(reverse('session_manager:session_info'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_active_sessions_staff_only(self):
        """Test that active sessions view requires staff permissions"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('session_manager:active_sessions'))
        self.assertEqual(response.status_code, 403)
    
    def test_active_sessions_staff_user(self):
        """Test active sessions view for staff user"""
        self.user.is_staff = True
        self.user.save()
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('session_manager:active_sessions'))
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('active_sessions', data)