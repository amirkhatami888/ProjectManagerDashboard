from django import forms
from django.utils.translation import gettext_lazy as _
from .models import (
    SubProject, SubProjectRejectionComment, SituationReport, 
    ProjectSituation, AdjustmentSituationReport, SubProjectGalleryImage,
    FinancialDocument, Payment, DocumentFile, FINANCIAL_DOCUMENT_TYPES
)
from .utils import jalali_to_gregorian
from django.core.exceptions import ValidationError
from jalali_date.fields import JalaliDateField
from jalali_date.widgets import AdminJalaliDateWidget
import jdatetime

# Custom file input widget for multiple file uploads
class MultipleFileInput(forms.FileInput):
    allow_multiple_selected = True

# Custom file field for multiple file uploads
class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
            
            # Check total file size (15MB limit)
            total_size = sum(file.size for file in result if file)
            max_size = 15 * 1024 * 1024  # 15MB in bytes
            
            if total_size > max_size:
                raise ValidationError(
                    f'مجموع حجم فایل‌های آپلود شده نباید از 15 مگابایت بیشتر باشد. '
                    f'حجم فعلی: {total_size / (1024 * 1024):.1f} مگابایت'
                )
            
            # Check individual file size (5MB per file)
            for file in result:
                if file and file.size > 5 * 1024 * 1024:  # 5MB per file
                    raise ValidationError(
                        f'حجم هر فایل نباید از 5 مگابایت بیشتر باشد. '
                        f'فایل "{file.name}" حجم آن {file.size / (1024 * 1024):.1f} مگابایت است.'
                    )
        else:
            result = single_file_clean(data, initial)
            if result and result.size > 5 * 1024 * 1024:  # 5MB per file
                raise ValidationError(
                    f'حجم فایل نباید از 5 مگابایت بیشتر باشد. '
                    f'حجم فعلی: {result.size / (1024 * 1024):.1f} مگابایت'
                )
        return result

class SubProjectForm(forms.ModelForm):
    # Define date fields separately to handle Persian dates
    start_date = forms.CharField(
        required=False,
        label=_('تاریخ شروع زیر پروژه'),
        widget=forms.TextInput(attrs={'class': 'form-control persian-date'}),
        help_text=_('تاریخ به فرمت شمسی (سال/ماه/روز)')
    )
    
    end_date = forms.CharField(
        required=False,
        label=_('تاریخ پایان زیر پروژه'),
        widget=forms.TextInput(attrs={'class': 'form-control persian-date'}),
        help_text=_('تاریخ به فرمت شمسی (سال/ماه/روز)')
    )
    
    contract_start_date = forms.CharField(
        required=False,
        label=_('تاریخ شروع قرارداد'),
        widget=forms.TextInput(attrs={'class': 'form-control persian-date'}),
        help_text=_('تاریخ به فرمت شمسی (سال/ماه/روز)')
    )
    
    contract_end_date = forms.CharField(
        required=False,
        label=_('تاریخ پایان قرارداد'),
        widget=forms.TextInput(attrs={'class': 'form-control persian-date'}),
        help_text=_('تاریخ به فرمت شمسی (سال/ماه/روز)')
    )
    
    class Meta:
        model = SubProject
        fields = [
            'sub_project_type', 
            'project', 
            'sub_project_number',
            # Date fields removed from model fields and handled separately
            # 'start_date',
            'state',
            'physical_progress',
            'remaining_work',
            'description',
            'is_suportting_charity',
            # 'contract_start_date',
            # 'contract_end_date',
            'contract_amount',
            'contract_type',
            'execution_method',
            'contractor_name',
            'contractor_id',
            'has_adjustment',
            'adjustment_coefficient',
            'imagenary_duration',
            'imagenrary_cost',
            'predicted_adjustment_amount',
        ]
        
        labels = {
            'sub_project_type': _('نوع زیرپروژه'),
            'project': _('پروژه اصلی'),
            'sub_project_number': _('اولویت زیرپروژه'),
            'state': _('وضعیت'),
            'physical_progress': _('پیشرفت فیزیکی (درصد)'),
            'remaining_work': _('کار باقیمانده'),
            'description': _('توضیحات'),
            'is_suportting_charity': _('مشارکت خیرین'),
            'contract_amount': _('مبلغ قرارداد (میلیون ریال)'),
            'contract_type': _('نوع قرارداد'),
            'execution_method': _('روش اجرا'),
            'contractor_name': _('نام پیمانکار'),
            'contractor_id': _('شناسه پیمانکار'),
            'has_adjustment': _('افزایش 25 درصدی قرار داد'),
            'adjustment_coefficient': _('درصد افزایش مبلغ قرار داد'),
            'imagenary_duration': _('مدت تخمینی (روز)'),
            'imagenrary_cost': _('هزینه تخمینی (ریال)'),
            'predicted_adjustment_amount': _('مجموع مبلغ پیشبینی شده ی تعدیل های تا انتهای پروژه'),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add Bootstrap classes to all fields
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            
        # Set initial values for Persian date fields from instance
        if self.instance and self.instance.pk:
            # Import our utility function for Gregorian to Jalali conversion
            from .utils import gregorian_to_jalali
            
            # Handle start_date
            if self.instance.start_date:
                self.initial['start_date'] = gregorian_to_jalali(self.instance.start_date)
                print(f"DEBUG: Set start_date initial value to {self.initial['start_date']} from {self.instance.start_date}")
                
            # Handle contract_start_date
            if self.instance.contract_start_date:
                self.initial['contract_start_date'] = gregorian_to_jalali(self.instance.contract_start_date)
                print(f"DEBUG: Set contract_start_date initial value to {self.initial['contract_start_date']} from {self.instance.contract_start_date}")
                
            # Handle contract_end_date
            if self.instance.contract_end_date:
                self.initial['contract_end_date'] = gregorian_to_jalali(self.instance.contract_end_date)
                print(f"DEBUG: Set contract_end_date initial value to {self.initial['contract_end_date']} from {self.instance.contract_end_date}")
                
            # Handle end_date if it exists
            if hasattr(self.instance, 'end_date') and self.instance.end_date:
                self.initial['end_date'] = gregorian_to_jalali(self.instance.end_date)
                print(f"DEBUG: Set end_date initial value to {self.initial['end_date']} from {self.instance.end_date}")

class SubProjectRejectionForm(forms.Form):
    FIELD_CHOICES = [
        ('sub_project_type', 'نوع زیرپروژه'),
        ('sub_project_number', 'اولویت زیرپروژه'),
        ('start_date', 'تاریخ شروع'),
        ('state', 'وضعیت'),
        ('physical_progress', 'پیشرفت فیزیکی'),
        ('remaining_work', 'کار باقیمانده'),
        ('description', 'توضیحات'),
        ('contract_start_date', 'تاریخ شروع قرارداد'),
        ('contract_end_date', 'تاریخ پایان قرارداد'),
        ('contract_amount', 'مبلغ قرارداد'),
        ('contract_type', 'نوع قرارداد'),
        ('execution_method', 'روش اجرا'),
        ('other', 'سایر موارد'),
    ]
    
    field_name = forms.ChoiceField(
        choices=FIELD_CHOICES,
        label="فیلد مورد نظر",
        widget=forms.Select(attrs={'class': 'form-control mb-3'})
    )
    comment = forms.CharField(
        label="توضیحات",
        widget=forms.Textarea(attrs={'class': 'form-control mb-3', 'rows': 4})
    )
    suggested_value = forms.CharField(
        label="مقدار پیشنهادی", 
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control mb-3'})
    )

class SituationReportForm(forms.ModelForm):
    allocation_date = forms.CharField(
        label='تاریخ',
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control persian-date',
            'placeholder': 'انتخاب تاریخ'
        })
    )
    
    report_number = forms.IntegerField(
        label='شماره صورت وضعیت',
        required=False,
        widget=forms.HiddenInput()
    )
    
    class Meta:
        model = SituationReport
        fields = [
            'report_number', 'allocation_type', 'allocation_date', 'description',
            'payment_amount_field'
        ]
        widgets = {
            'allocation_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'payment_amount_field': forms.NumberInput(attrs={'class': 'form-control', 'required': True})
        }
        labels = {
            'allocation_type': 'نوع صورت وضعیت کارکرد',
            'description': 'توضیحات',
            'payment_amount_field': 'مبلغ پرداختی'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control' 
                
        # Convert Gregorian date to Jalali for display if instance exists
        if self.instance and self.instance.pk and self.instance.allocation_date:
            from .utils import gregorian_to_jalali
            self.initial['allocation_date'] = gregorian_to_jalali(self.instance.allocation_date)
    
    def clean_allocation_date(self):
        allocation_date_str = self.cleaned_data.get('allocation_date')
        if not allocation_date_str:
            raise forms.ValidationError('تاریخ الزامی است.')
            
        try:
            from .utils import jalali_to_gregorian
            gregorian_date = jalali_to_gregorian(allocation_date_str)
            if not gregorian_date:
                raise forms.ValidationError('تاریخ نامعتبر است.')
            return gregorian_date
        except ValueError:
            raise forms.ValidationError('تاریخ نامعتبر است.')

class ProjectSituationForm(forms.ModelForm):
    report_date = forms.CharField(
        label=_('تاریخ گزارش'),
        widget=forms.TextInput(attrs={'class': 'form-control datepicker-input'})
    )
    
    class Meta:
        model = ProjectSituation
        fields = ['situation_type', 'description', 'report_date', 'is_resolved']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'situation_type': forms.Select(attrs={'class': 'form-control'}),
            'is_resolved': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_report_date(self):
        report_date_str = self.cleaned_data.get('report_date')
        if not report_date_str:
            return None
            
        try:
            return jalali_to_gregorian(report_date_str)
        except ValueError:
            raise forms.ValidationError('تاریخ نامعتبر است.')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Convert Gregorian date to Jalali for display
        if self.instance and self.instance.pk and self.instance.report_date:
            from .utils import gregorian_to_jalali
            self.initial['report_date'] = gregorian_to_jalali(self.instance.report_date) 

class AdjustmentSituationReportForm(forms.ModelForm):
    allocation_date = forms.CharField(
        label='تاریخ',
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control persian-date',
            'placeholder': 'انتخاب تاریخ'
        })
    )
    
    report_number = forms.IntegerField(
        label='شماره صورت وضعیت تعدیل',
        required=False,
        widget=forms.HiddenInput()
    )
    
    class Meta:
        model = AdjustmentSituationReport
        fields = [
            'report_number', 'allocation_date', 'description',
            'payment_amount_field'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'payment_amount_field': forms.NumberInput(attrs={'class': 'form-control', 'required': True})
        }
        labels = {
            'description': 'توضیحات',
            'payment_amount_field': 'مبلغ پرداختی'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control' 
                
        # Convert Gregorian date to Jalali for display if instance exists
        if self.instance and self.instance.pk and self.instance.allocation_date:
            from .utils import gregorian_to_jalali
            self.initial['allocation_date'] = gregorian_to_jalali(self.instance.allocation_date)
    
    def clean_allocation_date(self):
        allocation_date_str = self.cleaned_data.get('allocation_date')
        if not allocation_date_str:
            raise forms.ValidationError('تاریخ الزامی است.')
            
        try:
            from .utils import jalali_to_gregorian
            gregorian_date = jalali_to_gregorian(allocation_date_str)
            if not gregorian_date:
                raise forms.ValidationError('تاریخ نامعتبر است.')
            return gregorian_date
        except ValueError:
            raise forms.ValidationError('تاریخ نامعتبر است.') 

class SubProjectGalleryImageForm(forms.ModelForm):
    """Form for uploading gallery images for subprojects."""
    image = forms.ImageField(
        label="تصویر",
        help_text="لطفاً یک تصویر انتخاب کنید",
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = SubProjectGalleryImage
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'عنوان تصویر (اختیاری)'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'توضیحات تصویر (اختیاری)', 'rows': 3}),
        }

    def clean_image(self):
        """Validate image file."""
        image = self.cleaned_data.get('image')
        if image:
            # Optional: Add image validation
            if image.size > 5 * 1024 * 1024:  # 5MB limit
                raise forms.ValidationError("حجم تصویر نباید بیشتر از 5 مگابایت باشد.")
            
            # Optional: Check image type
            valid_types = ['image/jpeg', 'image/png', 'image/gif']
            if image.content_type not in valid_types:
                raise forms.ValidationError("فقط فایل های تصویری با فرمت JPEG, PNG و GIF مجاز هستند.")
        
        return image

class FinancialDocumentForm(forms.ModelForm):
    # Persian date pickers for dates
    jalali_contractor_date = forms.CharField(
        label=_('تاریخ ارسال سند مالی پیمان کار'),
        widget=forms.TextInput(attrs={'class': 'form-control persian-date'})
    )
    jalali_approval_date = forms.CharField(
        label=_('تاریخ تایید سند مالی'),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control persian-date'})
    )
    
    # Override amount fields as CharField to handle comma-separated values
    contractor_amount = forms.CharField(
        label=_('مبلغ ناخالص پیمان کار'),
        widget=forms.TextInput(attrs={
            'class': 'form-control currency-input', 
            'dir': 'ltr', 
            'style': 'text-align: left;',
            'placeholder': '0'
        })
    )
    approved_amount = forms.CharField(
        label=_('مبلغ ناخالص تایید شده'),
        widget=forms.TextInput(attrs={
            'class': 'form-control currency-input', 
            'dir': 'ltr', 
            'style': 'text-align: left;',
            'placeholder': '0'
        })
    )
    
    # Multiple file upload field
    files = MultipleFileField(
        label=_('مدارک'),
        required=False,
        widget=MultipleFileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png,.gif'
        })
    )
    
    class Meta:
        model = FinancialDocument
        fields = [
            'document_type', 'related_document', 'description'
        ]
        widgets = {
            'document_type': forms.Select(attrs={'class': 'form-control', 'required': True, 'id': 'id_document_type'}),
            'related_document': forms.Select(attrs={'class': 'form-control', 'id': 'id_related_document'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.subproject = kwargs.pop('subproject', None)
        super().__init__(*args, **kwargs)
        
        # Limit related document choices to the same subproject
        if self.subproject:
            self.fields['related_document'].queryset = FinancialDocument.objects.filter(
                subproject=self.subproject
            )
            
        # Initially hide related_document field, will be shown via JS when document_type is adjustment_report
        self.fields['related_document'].required = False
        
        # Initial date values if instance exists
        if self.instance.pk:
            if self.instance.contractor_submit_date:
                # Convert to jalali
                jalali_date = jdatetime.date.fromgregorian(date=self.instance.contractor_submit_date)
                self.fields['jalali_contractor_date'].initial = jalali_date.strftime('%Y/%m/%d')
            
            if self.instance.approval_date:
                # Convert to jalali
                jalali_date = jdatetime.date.fromgregorian(date=self.instance.approval_date)
                self.fields['jalali_approval_date'].initial = jalali_date.strftime('%Y/%m/%d')
            
            # Set initial values for amount fields with comma formatting
            if self.instance.contractor_amount:
                self.fields['contractor_amount'].initial = f"{self.instance.contractor_amount:,}"
            
            if self.instance.approved_amount:
                self.fields['approved_amount'].initial = f"{self.instance.approved_amount:,}"
        else:
            # Set default value for new instance - today's date
            today_jalali = jdatetime.date.today().strftime('%Y/%m/%d')
            self.fields['jalali_contractor_date'].initial = today_jalali
            self.fields['jalali_approval_date'].initial = today_jalali
    
    def clean_contractor_amount(self):
        amount = self.cleaned_data.get('contractor_amount')
        if amount:
            # Remove commas and convert to number
            try:
                amount_str = str(amount).replace(',', '').replace('٬', '')
                return int(amount_str)
            except (ValueError, TypeError):
                raise forms.ValidationError(_('مبلغ ناخالص پیمان کار نامعتبر است.'))
        return amount
    
    def clean_approved_amount(self):
        amount = self.cleaned_data.get('approved_amount')
        if amount:
            # Remove commas and convert to number
            try:
                amount_str = str(amount).replace(',', '').replace('٬', '')
                return int(amount_str)
            except (ValueError, TypeError):
                raise forms.ValidationError(_('مبلغ ناخالص تایید شده نامعتبر است.'))
        return amount

    def clean(self):
        cleaned_data = super().clean()
        
        # Check if jalali_contractor_date is provided
        jalali_contractor_date = cleaned_data.get('jalali_contractor_date')
        if jalali_contractor_date:
            try:
                # Convert Jalali date to Gregorian
                parts = jalali_contractor_date.split('/')
                if len(parts) == 3:
                    j_date = jdatetime.date(int(parts[0]), int(parts[1]), int(parts[2]))
                    g_date = j_date.togregorian()
                    # Set both date fields to ensure consistency
                    cleaned_data['contractor_date'] = g_date
                    cleaned_data['contractor_submit_date'] = g_date
                    self.instance.contractor_submit_date = g_date
                    self.instance.contractor_date = g_date
            except Exception as e:
                raise forms.ValidationError(_('تاریخ ارسال سند مالی پیمان کار نامعتبر است.'))
        else:
            raise forms.ValidationError(_('تاریخ ارسال سند مالی پیمان کار الزامی است.'))
        
        # Check if jalali_approval_date is provided
        jalali_approval_date = cleaned_data.get('jalali_approval_date')
        if jalali_approval_date:
            try:
                # Convert Jalali date to Gregorian
                parts = jalali_approval_date.split('/')
                if len(parts) == 3:
                    j_date = jdatetime.date(int(parts[0]), int(parts[1]), int(parts[2]))
                    g_date = j_date.togregorian()
                    cleaned_data['approval_date'] = g_date
                    self.instance.approval_date = g_date
            except Exception as e:
                raise forms.ValidationError(_('تاریخ تایید سند مالی نامعتبر است.'))
        else:
            # If approval date is not provided, use contractor date
            if 'contractor_date' in cleaned_data:
                cleaned_data['approval_date'] = cleaned_data['contractor_date']
                self.instance.approval_date = cleaned_data['contractor_date']
        
        # Make related_document required if document_type is adjustment_report
        document_type = cleaned_data.get('document_type')
        related_document = cleaned_data.get('related_document')
        
        if document_type == 'adjustment_report' and not related_document:
            self.add_error('related_document', _('برای صورت وضعیت تعدیل، انتخاب سند مالی مرتبط الزامی است.'))
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.subproject:
            instance.subproject = self.subproject
            
        # Set the amount fields from cleaned data
        if hasattr(self, 'cleaned_data'):
            if 'contractor_amount' in self.cleaned_data:
                instance.contractor_amount = self.cleaned_data['contractor_amount']
            if 'approved_amount' in self.cleaned_data:
                instance.approved_amount = self.cleaned_data['approved_amount']
            
            # Ensure contractor_submit_date is set to the same value as contractor_date
            if 'contractor_submit_date' in self.cleaned_data:
                instance.contractor_submit_date = self.cleaned_data['contractor_submit_date']
                
            # Ensure approval_date is set
            if 'approval_date' in self.cleaned_data:
                instance.approval_date = self.cleaned_data['approval_date']
            elif hasattr(instance, 'contractor_date') and instance.contractor_date:
                instance.approval_date = instance.contractor_date
        
        if commit:
            instance.save()
        return instance

class DocumentFileForm(forms.ModelForm):
    # No longer including 'file' directly as it's a BinaryField
    class Meta:
        model = DocumentFile
        fields = ['document', 'filename', 'file_mime_type'] # Removed 'uploaded_at'
        widgets = {
            'document': forms.HiddenInput(), # Assuming document is set in the view
            'file_mime_type': forms.HiddenInput(), # Set in view
        }

class PaymentForm(forms.ModelForm):
    # Persian date picker for payment date
    jalali_payment_date = forms.CharField(
        label=_('تاریخ پرداختی'),
        widget=forms.TextInput(attrs={'class': 'jalali-datepicker form-control'})
    )
    
    class Meta:
        model = Payment
        fields = ['amount', 'related_document', 'description']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'related_document': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.subproject = kwargs.pop('subproject', None)
        super().__init__(*args, **kwargs)
        
        # Limit related_document choices to the same subproject
        if self.subproject:
            self.fields['related_document'].queryset = FinancialDocument.objects.filter(
                subproject=self.subproject
            )
        
        # Initial date value if instance exists
        if self.instance.pk and self.instance.payment_date:
            # Convert to jalali
            jalali_date = jdatetime.date.fromgregorian(date=self.instance.payment_date)
            self.fields['jalali_payment_date'].initial = jalali_date.strftime('%Y/%m/%d')
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Convert jalali date to gregorian
        jalali_payment_date = cleaned_data.get('jalali_payment_date')
        if jalali_payment_date:
            try:
                # Parse jalali date
                jalali_parts = jalali_payment_date.split('/')
                jalali_year = int(jalali_parts[0])
                jalali_month = int(jalali_parts[1])
                jalali_day = int(jalali_parts[2])
                
                # Convert to gregorian
                gregorian_date = jdatetime.date(jalali_year, jalali_month, jalali_day).togregorian()
                cleaned_data['payment_date'] = gregorian_date
            except (ValueError, IndexError):
                self.add_error('jalali_payment_date', _('تاریخ نامعتبر'))
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.subproject:
            instance.subproject = self.subproject
        
        if commit:
            instance.save()
        return instance 