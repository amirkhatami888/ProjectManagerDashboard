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
            'thumbnail_size',
            'enable_image_compression',
            'allowed_image_formats',
            'show_image_titles',
            'show_image_descriptions',
            'show_upload_dates',
            'images_per_row',
            'enable_lightbox',
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
            'thumbnail_size': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 50,
                'max': 500,
                'step': 10
            }),
            'images_per_row': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 6,
                'step': 1
            }),
            'enable_image_compression': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'show_image_titles': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'show_image_descriptions': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'show_upload_dates': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'enable_lightbox': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'max_images_per_page': _('حداکثر تعداد تصاویر در هر صفحه'),
            'max_image_size_mb': _('حداکثر حجم تصویر (مگابایت)'),
            'thumbnail_size': _('اندازه تصاویر کوچک (پیکسل)'),
            'enable_image_compression': _('فشرده‌سازی خودکار تصاویر'),
            'allowed_image_formats': _('فرمت‌های مجاز تصاویر'),
            'show_image_titles': _('نمایش عنوان تصاویر'),
            'show_image_descriptions': _('نمایش توضیحات تصاویر'),
            'show_upload_dates': _('نمایش تاریخ آپلود'),
            'images_per_row': _('تعداد تصاویر در هر ردیف'),
            'enable_lightbox': _('فعال‌سازی نمایش بزرگ تصاویر'),
        }
        help_texts = {
            'max_images_per_page': _('تعداد تصاویری که در هر صفحه گالری نمایش داده می‌شود'),
            'max_image_size_mb': _('حداکثر حجم مجاز برای هر تصویر در مگابایت'),
            'thumbnail_size': _('اندازه تصاویر کوچک در پیکسل'),
            'enable_image_compression': _('تصاویر به صورت خودکار فشرده می‌شوند'),
            'allowed_image_formats': _('لیست فرمت‌های مجاز برای آپلود تصاویر'),
            'show_image_titles': _('عنوان تصاویر در گالری نمایش داده می‌شود'),
            'show_image_descriptions': _('توضیحات تصاویر در گالری نمایش داده می‌شود'),
            'show_upload_dates': _('تاریخ آپلود تصاویر نمایش داده می‌شود'),
            'images_per_row': _('تعداد تصاویری که در هر ردیف نمایش داده می‌شود'),
            'enable_lightbox': _('امکان نمایش تصاویر در اندازه بزرگ فعال است'),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Customize allowed_image_formats field
        self.fields['allowed_image_formats'].widget = forms.CheckboxSelectMultiple(
            choices=[
                ('image/jpeg', 'JPEG'),
                ('image/png', 'PNG'),
                ('image/gif', 'GIF'),
                ('image/webp', 'WebP'),
                ('image/bmp', 'BMP'),
                ('image/tiff', 'TIFF'),
            ],
            attrs={'class': 'form-check-input'}
        )
        
        # Add CSS classes to form fields
        for field_name, field in self.fields.items():
            if field_name not in ['enable_image_compression', 'show_image_titles', 
                                'show_image_descriptions', 'show_upload_dates', 'enable_lightbox']:
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
    
    def clean_thumbnail_size(self):
        value = self.cleaned_data.get('thumbnail_size')
        if value and (value < 50 or value > 500):
            raise forms.ValidationError('اندازه تصاویر کوچک باید بین 50 تا 500 پیکسل باشد.')
        return value
    
    def clean_images_per_row(self):
        value = self.cleaned_data.get('images_per_row')
        if value and (value < 1 or value > 6):
            raise forms.ValidationError('تعداد تصاویر در هر ردیف باید بین 1 تا 6 باشد.')
        return value
