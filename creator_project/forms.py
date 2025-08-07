from django import forms
from .models import Project, FundingRequest
from creator_program.models import Program
from .models import ProjectFinancialAllocation

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            'program', 'name', 'project_type', 'province', 'city', 
            'area_size', 'site_area', 'wall_length', 'notables', 'floor', 'physical_progress', 'estimated_opening_time', 
            'overall_status'
        ]
        widgets = {
            'program': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'project_type': forms.Select(attrs={'class': 'form-control'}),
            'province': forms.Select(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'area_size': forms.NumberInput(attrs={'class': 'form-control'}),
            'site_area': forms.NumberInput(attrs={'class': 'form-control'}),
            'wall_length': forms.NumberInput(attrs={'class': 'form-control'}),
            'notables': forms.NumberInput(attrs={'class': 'form-control'}),
            'floor': forms.NumberInput(attrs={'class': 'form-control'}),
            'physical_progress': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100, 'step': '0.01'}),
            'estimated_opening_time': forms.DateInput(attrs={'class': 'form-control datepicker'}),
            'overall_status': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'program': 'طرح',
            'name': 'نام پروژه',
            'project_type': 'نوع پروژه',
            'province': 'استان',
            'city': 'شهر',
            'area_size': 'عرصه',
            'site_area': 'مساحت محوطه سازی',
            'wall_length': 'طول دیوار کشی',
            'notables': 'اعیان',
            'floor': 'طبقه',
            'physical_progress': 'پیشرفت فیزیکی (٪)',
            'estimated_opening_time': 'تاریخ پایان پروژه',
            'overall_status': 'وضعیت کلی',
        }

    def __init__(self, *args, **kwargs):
        # Extract the user parameter if it exists
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Make program field required
        self.fields['program'].required = True
        
        # Make province and city fields not required since they will be set automatically
        self.fields['province'].required = False
        self.fields['city'].required = False
        
        # Make physical_progress and overall_status not required since they have default values
        self.fields['physical_progress'].required = False
        self.fields['overall_status'].required = False
        
        # Make province and city fields read-only as they will be set automatically from the program
        self.fields['province'].widget.attrs['readonly'] = True
        self.fields['province'].widget.attrs['disabled'] = True
        self.fields['province'].help_text = 'استان به صورت خودکار از طرح انتخاب شده تنظیم می‌شود'
        
        self.fields['city'].widget.attrs['readonly'] = True
        self.fields['city'].widget.attrs['disabled'] = True
        self.fields['city'].help_text = 'شهر به صورت خودکار از طرح انتخاب شده تنظیم می‌شود'
        
        # Filter programs based on user if provided
        if user:
            # If the user is a province manager, only show programs created by this user
            if hasattr(user, 'is_province_manager') and user.is_province_manager:
                self.fields['program'].queryset = Program.objects.filter(created_by=user)
            # For other roles (admin, etc.), show all programs
            # You can customize this logic based on your requirements

    def clean(self):
        cleaned_data = super().clean()
        program = cleaned_data.get('program')
        
        if program:
            # Automatically set province and city from the selected program
            cleaned_data['province'] = program.province
            cleaned_data['city'] = program.city
        
        # Set default values for fields that might not be provided
        if not cleaned_data.get('physical_progress'):
            cleaned_data['physical_progress'] = 0
        if not cleaned_data.get('overall_status'):
            cleaned_data['overall_status'] = 'غیره فعال'
        
        return cleaned_data


class FundingRequestForm(forms.ModelForm):
    # Override province_suggested_amount as CharField to handle comma-separated values
    province_suggested_amount = forms.CharField(
        label='مبلغ پیشنهادی (ریال)',
        widget=forms.TextInput(attrs={
            'class': 'form-control currency-input',
            'dir': 'ltr',
            'style': 'text-align: left;',
            'placeholder': '0'
        })
    )
    
    class Meta:
        model = FundingRequest
        fields = ['project', 'province_suggested_amount', 'priority', 'province_description']
        widgets = {
            'project': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'province_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'project': 'پروژه',
            'priority': 'اولویت',
            'province_description': 'توضیحات',
        }
    
    def __init__(self, *args, **kwargs):
        # Extract the user parameter if it exists
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter projects based on user if provided
        if user:
            # If the user is a province manager, only show projects in their province
            if hasattr(user, 'is_province_manager') and user.is_province_manager:
                user_provinces = user.get_assigned_provinces() if hasattr(user, 'get_assigned_provinces') else []
                if not user_provinces and user.province:
                    user_provinces = [user.province]
                
                if user_provinces:
                    self.fields['project'].queryset = Project.objects.filter(province__in=user_provinces)
        
        # Set initial value for amount field with comma formatting if instance exists
        if self.instance.pk and self.instance.province_suggested_amount:
            self.fields['province_suggested_amount'].initial = f"{self.instance.province_suggested_amount:,}"
    
    def clean_province_suggested_amount(self):
        amount = self.cleaned_data.get('province_suggested_amount')
        if amount:
            # Remove commas and convert to number
            try:
                amount_str = str(amount).replace(',', '').replace('٬', '')
                return int(amount_str)
            except (ValueError, TypeError):
                raise forms.ValidationError('مبلغ پیشنهادی نامعتبر است.')
        return amount


class ExpertFundingReviewForm(forms.ModelForm):
    # Override headquarters_suggested_amount as CharField to handle comma-separated values
    headquarters_suggested_amount = forms.CharField(
        label='مبلغ پیشنهادی ستاد (ریال)',
        widget=forms.TextInput(attrs={
            'class': 'form-control currency-input',
            'dir': 'ltr',
            'style': 'text-align: left;',
            'placeholder': '0'
        })
    )
    
    # Action field for approve/reject decision
    action = forms.ChoiceField(
        choices=[
            ('approve', 'تایید درخواست'),
            ('reject', 'رد درخواست'),
        ],
        label='تصمیم کارشناسی',
        widget=forms.HiddenInput(),
        initial='approve'
    )
    
    # Rejection reason field
    expert_rejection_reason = forms.CharField(
        label='دلیل رد درخواست',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'لطفاً دلایل رد درخواست را به صورت کامل و واضح بنویسید...'
        })
    )
    
    class Meta:
        model = FundingRequest
        fields = ['headquarters_suggested_amount', 'expert_description']
        widgets = {
            'expert_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'expert_description': 'توضیحات کارشناس',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set initial value for amount field with comma formatting if instance exists
        if self.instance.pk and self.instance.headquarters_suggested_amount:
            self.fields['headquarters_suggested_amount'].initial = f"{self.instance.headquarters_suggested_amount:,}"
    
    def clean_headquarters_suggested_amount(self):
        amount = self.cleaned_data.get('headquarters_suggested_amount')
        if amount:
            # Remove commas and convert to number
            try:
                amount_str = str(amount).replace(',', '').replace('٬', '')
                return int(amount_str)
            except (ValueError, TypeError):
                raise forms.ValidationError('مبلغ پیشنهادی ستاد نامعتبر است.')
        return amount
    
    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        rejection_reason = cleaned_data.get('expert_rejection_reason')
        
        # If action is reject, rejection reason is required
        if action == 'reject' and not rejection_reason:
            raise forms.ValidationError({
                'expert_rejection_reason': 'در صورت رد درخواست، دلیل رد الزامی است.'
            })
        
        return cleaned_data


class ChiefFundingReviewForm(forms.ModelForm):
    # Override final_amount as CharField to handle comma-separated values
    final_amount = forms.CharField(
        label='مبلغ نهایی مصوب (ریال)',
        widget=forms.TextInput(attrs={
            'class': 'form-control currency-input',
            'dir': 'ltr',
            'style': 'text-align: left;',
            'placeholder': '0'
        })
    )
    
    # Action field for approve/reject decision
    action = forms.ChoiceField(
        choices=[
            ('approve', 'تایید درخواست'),
            ('reject', 'رد درخواست'),
        ],
        label='تصمیم نهایی',
        widget=forms.HiddenInput(),
        initial='approve'
    )
    
    # Rejection reason field
    chief_rejection_reason = forms.CharField(
        label='دلیل رد درخواست',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'لطفاً دلایل رد درخواست را به صورت کامل و واضح بنویسید...'
        })
    )
    
    class Meta:
        model = FundingRequest
        fields = ['final_amount']
        labels = {}
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set initial value for amount field with comma formatting if instance exists
        if self.instance.pk and self.instance.final_amount:
            self.fields['final_amount'].initial = f"{self.instance.final_amount:,}"
    
    def clean_final_amount(self):
        amount = self.cleaned_data.get('final_amount')
        if amount:
            # Remove commas and convert to number
            try:
                amount_str = str(amount).replace(',', '').replace('٬', '')
                return int(amount_str)
            except (ValueError, TypeError):
                raise forms.ValidationError('مبلغ نهایی مصوب نامعتبر است.')
        return amount
    
    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        rejection_reason = cleaned_data.get('chief_rejection_reason')
        
        # If action is reject, rejection reason is required
        if action == 'reject' and not rejection_reason:
            raise forms.ValidationError({
                'chief_rejection_reason': 'در صورت رد درخواست، دلیل رد الزامی است.'
            })
        
        return cleaned_data


class ProjectRejectionForm(forms.Form):
    comment = forms.CharField(
        label="توضیحات",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'لطفا دلایل رد پروژه و اصلاحات مورد نیاز را به صورت دقیق بنویسید...'}),
        required=True,
        help_text="لطفا دلایل رد پروژه و اصلاحات مورد نیاز را به صورت دقیق بنویسید."
    )


class ProjectFinancialAllocationForm(forms.ModelForm):
    """Form for adding financial allocations to projects"""
    
    # Override amount as CharField to handle comma-separated values
    amount = forms.CharField(
        label='مبلغ تخصیص (ریال)',
        widget=forms.TextInput(attrs={
            'class': 'form-control currency-input currency-input-enhanced',
            'dir': 'ltr',
            'style': 'text-align: left;',
            'placeholder': '0',
            'autocomplete': 'off',
            'data-currency-field': 'true'
        })
    )
    
    class Meta:
        model = ProjectFinancialAllocation
        fields = ['amount', 'allocation_type', 'letter_number', 'description']
        widgets = {
            'amount': forms.TextInput(attrs={
                'class': 'form-control currency-input currency-input-enhanced',
                'dir': 'ltr',
                'style': 'text-align: left;',
                'placeholder': '0',
                'autocomplete': 'off',
                'data-currency-field': 'true'
            }),
            'allocation_type': forms.Select(attrs={'class': 'form-control'}),
            'letter_number': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'توضیحات اختیاری در مورد تخصیص مالی...'
            }),
        }
        labels = {
            'amount': 'مبلغ تخصیص (ریال)',
            'allocation_type': 'نوع تخصیص',
            'letter_number': 'شماره نامه',
            'description': 'توضیحات',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set initial value for amount field with comma formatting if instance exists
        if self.instance.pk and self.instance.amount:
            self.fields['amount'].initial = f"{self.instance.amount:,}"
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount:
            # Remove commas and convert to number
            try:
                amount_str = str(amount).replace(',', '').replace('٬', '')
                return int(amount_str)
            except (ValueError, TypeError):
                raise forms.ValidationError('مبلغ تخصیص نامعتبر است.')
        return amount
    
    def clean_allocation_date(self):
        """Handle allocation_date field manually since it's not in Meta fields"""
        allocation_date = self.data.get('allocation_date')
        if allocation_date:
            try:
                # Parse Persian date (format: YYYY/MM/DD)
                parts = allocation_date.split('/')
                if len(parts) == 3:
                    import jdatetime
                    j_date = jdatetime.date(int(parts[0]), int(parts[1]), int(parts[2]))
                    g_date = j_date.togregorian()
                    return g_date
            except (ValueError, TypeError):
                raise forms.ValidationError('تاریخ تخصیص نامعتبر است.')
        return None