from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User

class CustomUserCreationForm(UserCreationForm):
    """Custom form for creating new users with our custom fields"""
    class Meta:
        model = User
        fields = ('username', 'email', 'role', 'province')
        
class CustomUserChangeForm(UserChangeForm):
    """Custom form for updating users with our custom fields"""
    class Meta:
        model = User
        fields = ('username', 'email', 'role', 'province', 'phone_number')

class UserProfileForm(forms.ModelForm):
    """Form for user to update their profile information"""
    class Meta:
        model = User
        fields = ('username', 'email', 'phone_number', 'profile_picture', 'نام', 'نام_خانوادگی', 'سمت')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مثال: 09123456789'}),
            'نام': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام خود را وارد کنید'}),
            'نام_خانوادگی': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام خانوادگی خود را وارد کنید'}),
            'سمت': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'سمت شغلی خود را وارد کنید'}),
        }
    
    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        self.fields['profile_picture'].widget.attrs.update({'class': 'form-control'})
        # Make username read-only for security but keep it visible
        self.fields['username'].disabled = True 

    def clean(self):
        cleaned_data = super().clean()
        
        # Normalize province name
        province = cleaned_data.get('province')
        if province:
            # Find the exact match in PROVINCE_CHOICES
            normalized_province = next(
                (choice[0] for choice in User.PROVINCE_CHOICES if choice[0].replace(' ', '') == province.replace(' ', '')), 
                province
            )
            cleaned_data['province'] = normalized_province
        
        return cleaned_data 