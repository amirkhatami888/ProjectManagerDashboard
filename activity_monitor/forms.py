from django import forms
from django.utils.translation import gettext_lazy as _
from .models import GallerySettings


class GallerySettingsForm(forms.ModelForm):
    """Form for configuring gallery settings"""
    
    class Meta:
        model = GallerySettings
        fields = [
            'max_images_per_page',
            'max_image_size_mb', 
            'max_upload_images',
            'max_total_size_mb',
            'enable_image_compression',
        ]
        widgets = {
            'max_images_per_page': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 100,
                'step': 1
            }),
            'max_image_size_mb': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 50,
                'step': 1
            }),
            'max_upload_images': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 1000,
                'step': 1
            }),
            'max_total_size_mb': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 1000,
                'step': 1
            }),
            'enable_image_compression': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'max_images_per_page': _('حداکثر تعداد تصاویر در هر صفحه'),
            'max_image_size_mb': _('حداکثر حجم هر تصویر (مگابایت)'),
            'max_upload_images': _('حداکثر تعداد تصاویر قابل آپلود'),
            'max_total_size_mb': _('حداکثر حجم کل تصاویر (مگابایت)'),
            'enable_image_compression': _('فشرده‌سازی خودکار تصاویر'),
        }
        help_texts = {
            'max_images_per_page': _('تعداد تصاویری که در هر صفحه گالری نمایش داده می‌شود'),
            'max_image_size_mb': _('حداکثر حجم مجاز برای هر تصویر در مگابایت'),
            'max_upload_images': _('حداکثر تعداد تصاویری که می‌توان در یک پروژه آپلود کرد'),
            'max_total_size_mb': _('حداکثر حجم کل تصاویر یک پروژه در مگابایت'),
            'enable_image_compression': _('تصاویر به صورت خودکار فشرده می‌شوند'),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add CSS classes to form fields
        for field_name, field in self.fields.items():
            if field_name not in ['enable_image_compression']:
                if not hasattr(field.widget, 'attrs'):
                    field.widget.attrs = {}
                field.widget.attrs['class'] = 'form-control'
    
    def clean_max_images_per_page(self):
        value = self.cleaned_data.get('max_images_per_page')
        if value and (value < 1 or value > 100):
            raise forms.ValidationError('تعداد تصاویر باید بین 1 تا 100 باشد.')
        return value
    
    def clean_max_image_size_mb(self):
        value = self.cleaned_data.get('max_image_size_mb')
        if value and (value < 1 or value > 50):
            raise forms.ValidationError('حجم تصویر باید بین 1 تا 50 مگابایت باشد.')
        return value
    
    def clean_max_upload_images(self):
        value = self.cleaned_data.get('max_upload_images')
        if value and (value < 1 or value > 1000):
            raise forms.ValidationError('تعداد تصاویر قابل آپلود باید بین 1 تا 1000 باشد.')
        return value
    
    def clean_max_total_size_mb(self):
        value = self.cleaned_data.get('max_total_size_mb')
        if value and (value < 1 or value > 1000):
            raise forms.ValidationError('حجم کل تصاویر باید بین 1 تا 1000 مگابایت باشد.')
        return value
