from django import forms
from .models import Program
import logging

logger = logging.getLogger(__name__)


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
        
        # Handle province restrictions based on user role and province assignments
        if user:
            # Get user's assigned provinces
            assigned_provinces = user.get_assigned_provinces()
            
            # If user has specific province assignments, restrict choices
            if assigned_provinces and not (user.is_admin or user.is_ceo or user.is_chief_executive):
                # Create choices from the user's assigned provinces
                province_choices = [(province, province) for province in assigned_provinces]
                self.fields['province'].choices = province_choices
                
                # Set initial value to the first assigned province if creating new program
                if not self.instance.pk and assigned_provinces:
                    self.fields['province'].initial = assigned_provinces[0]
                
                # Make the field read-only if there's only one choice
                if len(assigned_provinces) == 1:
                    self.fields['province'].widget.attrs['readonly'] = True
                    self.fields['province'].help_text = f'شما فقط به استان {assigned_provinces[0]} دسترسی دارید'
    
    def clean_province(self):
        """Custom validation for province field with debugging"""
        province = self.cleaned_data.get('province')
        logger.info(f"DEBUG: Submitted province value: '{province}' (repr: {repr(province)})")
        
        # Check if the province is in the available choices
        available_choices = [choice[0] for choice in self.fields['province'].choices]
        logger.info(f"DEBUG: Available province choices: {available_choices}")
        
        if province and province not in available_choices:
            logger.error(f"DEBUG: Province '{province}' not found in available choices: {available_choices}")
            raise forms.ValidationError(f"استان '{province}' در لیست استان‌های مجاز نیست.")
        
        return province
    
    def clean(self):
        """Additional validation for the entire form"""
        cleaned_data = super().clean()
        
        # Add any additional validation logic here if needed
        # For example, you could validate that longitude and latitude are within valid ranges
        
        return cleaned_data