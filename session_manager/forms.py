from django import forms
from django.contrib.auth.models import User

class SessionManagementForm(forms.Form):
    """Form for session management operations"""
    
    session_key = forms.CharField(
        max_length=40,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter session key'
        }),
        help_text='Session key to terminate'
    )
    
    def clean_session_key(self):
        session_key = self.cleaned_data.get('session_key')
        if session_key and len(session_key) != 40:
            raise forms.ValidationError('Session key must be 40 characters long')
        return session_key

class UserSessionForm(forms.Form):
    """Form for user session operations"""
    
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Select a user",
        help_text='User to manage sessions for'
    )
    
    action = forms.ChoiceField(
        choices=[
            ('view', 'View Sessions'),
            ('terminate_all', 'Terminate All Sessions'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text='Action to perform'
    )
