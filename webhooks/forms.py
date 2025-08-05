from django import forms
from .models import WebhookConfiguration


class WebhookConfigurationForm(forms.ModelForm):
    """
    Form for creating and editing webhook configurations
    """
    class Meta:
        model = WebhookConfiguration
        fields = ['repository_url', 'secret_token', 'is_active', 'auto_deploy', 'deploy_branch']
        widgets = {
            'repository_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://github.com/username/repository'
            }),
            'secret_token': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'GitHub webhook secret token'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'auto_deploy': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'deploy_branch': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'main'
            }),
        }
    
    def clean_repository_url(self):
        """
        Validate repository URL format
        """
        url = self.cleaned_data['repository_url']
        if not url.startswith(('https://github.com/', 'https://www.github.com/')):
            raise forms.ValidationError('Please enter a valid GitHub repository URL.')
        return url
    
    def clean_secret_token(self):
        """
        Secret token is optional but should be secure if provided
        """
        token = self.cleaned_data['secret_token']
        if token and len(token) < 10:
            raise forms.ValidationError('Secret token should be at least 10 characters long.')
        return token 