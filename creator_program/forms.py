from django import forms
from .models import Program


class ProgramForm(forms.ModelForm):
    class Meta:
        model = Program
        fields = ['title', 'program_type', 'province', 'city', 'address', 'longitude', 'latitude', 'license_state', 'license_code', 'description', 'program_opening_date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'program_type': forms.Select(attrs={'class': 'form-control'}),
            'province': forms.Select(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
            'license_state': forms.Select(attrs={'class': 'form-control'}),
            'license_code': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'program_opening_date': forms.DateInput(attrs={
                'class': 'form-control', 
                'readonly': True,
                'placeholder': 'این فیلد به صورت خودکار بر اساس تاریخ پایان پروژه‌ها محاسبه می‌شود'
            }),
        }
        labels = {
            'title': 'عنوان طرح',
            'program_type': 'نوع طرح',
            'province': 'استان',
            'city': 'شهر',
            'address': 'آدرس',
            'longitude': 'طول جغرافیایی',
            'latitude': 'عرض جغرافیایی',
            'license_state': 'وضعیت مجوز دفترچه توجیهی',
            'license_code': 'کد مجوز دفترچه توجیهی',
            'description': 'توضیحات',
            'program_opening_date': 'تاریخ افتتاح طرح (محاسبه خودکار)',
        }
    
    def __init__(self, *args, **kwargs):
        # Extract the user parameter if it exists
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Add help text for program_opening_date
        self.fields['program_opening_date'].help_text = 'این فیلد به صورت خودکار بر اساس تاریخ پایان پروژه‌های این طرح محاسبه می‌شود'
        
        # If user is a province manager, restrict province choices to their province
        if user and hasattr(user, 'is_province_manager') and user.is_province_manager and user.province:
            # Create a list with only the user's province
            province_choices = [(user.province, user.province)]
            self.fields['province'].choices = province_choices
            self.fields['province'].initial = user.province
            # Make the field read-only since there's only one choice
            self.fields['province'].widget.attrs['readonly'] = True