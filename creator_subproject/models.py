from django.db import models
from django.conf import settings
from django.utils import timezone
# Remove direct import of Project
# from creator_project.models import Project
from django.db.models import Sum
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
import json
from .utils import gregorian_to_jalali
from django.db.models import Q
from decimal import Decimal
import datetime
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from creator_project.models import Project

User = get_user_model()

# Define Financial Document Type choices
FINANCIAL_DOCUMENT_TYPES = (
    ('advance_payment', 'پیش پرداخت'),
    ('temporary_report', 'صورت وضعیت موقت'),
    ('permanent_report', 'صورت وضعیت دائم'),
    ('adjustment_report', 'صورت وضعیت تعدیل'),
)

class SubProject(models.Model):
    # Changed to match the previous executive_stage choices
    SUB_PROJECT_TYPE_CHOICES = [
        ('فاز مطالعاتی', 'فاز مطالعاتی'),
        ('طراحی نقشه های فاز 1و2', 'طراحی نقشه های فاز 1و2'),
        ('برگزاری مناقصه', 'برگزاری مناقصه'),
        ('انعقاد قرار داد و تحویل زمین', 'انعقاد قرار داد و تحویل زمین'),
        ('تجهیزات کارگاهی', 'تجهیزات کارگاهی'),
        ('گودبرداری', 'گودبرداری'),
        ('فونداسیون', 'فونداسیون'),
        ('اسکلت', 'اسکلت'),
        ('سفت کاری', 'سفت کاری'),
        ('نما', 'نما'),
        ('اجرای تاسیسات', 'اجرای تاسیسات'),
        ('نازک کاری', 'نازک کاری'),
        ('اجرای نصبیات برقی و مکانیکی', 'اجرای نصبیات برقی و مکانیکی'),
        ('محوطه سازی', 'محوطه سازی'),
        ('دیوارکشی', 'دیوارکشی'),
        ('محوطه سازی و دیوار کشی', 'محوطه سازی و دیوار کشی'),
    ]
    
    STATE_CHOICES = [
        ('فعال', 'فعال'),
        ('غیرفعال-ختم پیمان', 'غیرفعال-ختم پیمان'),
        ('غیر فعال- ماده 46', 'غیر فعال- ماده 46'),
        ('غیره فعال-تعلیق', 'غیره فعال-تعلیق'),
        ('غیره فعال-اتمام قرار داد', 'غیره فعال-اتمام قرار داد'),
        ('تحویل موقت', 'تحویل موقت'),
        ('تحویل قطعی', 'تحویل قطعی'),
        ('تامین اعتبار', 'تامین اعتبار'),
    ]
    
    # EXECUTIVE_STAGE_CHOICES removed - field moved to sub_project_type
    
    CONTRACT_TYPE_CHOICES = [
        ('سرجمع', 'سرجمع'),
        ('فرست بها', 'فرست بها'),
        ('پیمان مدیریت', 'پیمان مدیریت'),
        ('مشارکت در ساخت', 'مشارکت در ساخت'),
        ('خیر ساز', 'خیر ساز'),
        ('BOT', 'BOT'),
        ('EPC', 'EPC'),
        ('EC', 'EC'),
        ('امانی', 'امانی'),
        ('فاقد قرارداد', 'فاقد قرارداد'),
    ]
    
    EXECUTION_METHOD_CHOICES = [
        ('مناقصه عمومی- سه عاملی', 'مناقصه عمومی- سه عاملی'),
        ('ترک تشریفات -سه عاملی', 'ترک تشریفات -سه عاملی'),
        ('مناقصه محدود-سه عاملی', 'مناقصه محدود-سه عاملی'),
        ('مناقصه عمومی نظارت دفترفنی استان', 'مناقصه عمومی نظارت دفترفنی استان'),
        ('ترک تشریفات نظارت دفترفنی استان', 'ترک تشریفات نظارت دفترفنی استان'),
        ('مناقصه محدود نظارت دفترفنی استان', 'مناقصه محدود نظارت دفترفنی استان'),
        ('استعلام بها نظارت دفترفنی استان', 'استعلام بها نظارت دفترفنی استان'),
    ]
    
    CHARITY_STATE_CHOICES = [
        ('دارد', 'دارد'),
        ('ندارد', 'ندارد')
    ]
    
    HAS_ADJUSTMENT_CHOICES = [
        ('دارد', 'دارد'),
        ('ندارد', 'ندارد')
    ]
    
    # New choices for 25% increase
    HAS_25_PERCENT_INCREASE_CHOICES = [
        ('دارد', 'دارد'),
        ('ندارد', 'ندارد')
    ]
    
    # New choices for subproject relationship
    RELATIONSHIP_TYPE_CHOICES = [
        ('شروع با', 'شروع با'),
        ('پایان با', 'پایان با'),
        ('بعد از', 'بعد از'),
        ('قبل از', 'قبل از'),
        ('شناور', 'شناور'),
    ]
    
    # New choices for transaction threshold
    TRANSACTION_THRESHOLD_CHOICES = [
        ('کوچک', 'کوچک'),
        ('متوسط', 'متوسط'),
        ('بزرگ', 'بزرگ'),
    ]
    
    # Tender type choices
    TENDER_TYPE_CHOICES = [
        ('عمومی-یک مرحله ای', 'عمومی-یک مرحله ای'),
        ('عمومی- دومرحله ای', 'عمومی- دومرحله ای'),
        ('ترک تشریفات', 'ترک تشریفات'),
        ('استعلام بهای متوسط', 'استعلام بهای متوسط'),
        ('معامله بر خط', 'معامله بر خط'),
    ]
    
    # Has consultant choices
    HAS_CONSULTANT_CHOICES = [
        ('دارد', 'دارد'),
        ('ندارد', 'ندارد'),
    ]
    
    # Main fields
    project = models.ForeignKey('creator_project.Project', on_delete=models.CASCADE, related_name='subprojects')
    name = models.CharField(max_length=255, blank=True, null=True, verbose_name="نام زیرپروژه")
    sub_project_type = models.CharField(max_length=100, choices=SUB_PROJECT_TYPE_CHOICES, verbose_name="نوع زیرپروژه")
    sub_project_number = models.PositiveSmallIntegerField(help_text="Must be between 1-5")
    start_date = models.DateField(null=True, blank=True, verbose_name="تاریخ شروع زیر پروژه")
    end_date = models.DateField(null=True, blank=True, verbose_name="تاریخ پایان زیر پروژه")
    state = models.CharField(max_length=100, choices=STATE_CHOICES)
    physical_progress = models.DecimalField(max_digits=5, decimal_places=2, default=0,null=True, blank=True)
    # executive_stage field removed - functionality moved to sub_project_type
    remaining_work = models.TextField(null=True, blank=True)
    is_suportting_charity = models.CharField(max_length=25, choices=CHARITY_STATE_CHOICES, default='ندارد', verbose_name="مشارکت خیرین")
    description = models.TextField(null=True, blank=True, verbose_name="توضیحات")
    
    # Fields for subproject relationships
    related_subproject = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='dependent_subprojects', verbose_name="ارتباط زیر پروژه")
    relationship_type = models.CharField(max_length=20, choices=RELATIONSHIP_TYPE_CHOICES, null=True, blank=True, verbose_name="نوع ارتباط")
    relationship_delay = models.IntegerField(null=True, blank=True, verbose_name="تعجیل وتاخیر ارتباط زیر پروژه")
    
    # Fields for subprojects without contracts
    imagenary_duration = models.PositiveIntegerField(null=True, blank=True, verbose_name="مدت تخمینی (روز)")
    imagenrary_cost = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name="هزینه تخمینی (ریال)")
    
    # Method of calculating approximate cost
    cost_calculation_method = models.TextField(
        null=True, 
        blank=True, 
        verbose_name="روش محاسبه هزینه تقریبی"
    )
    
    # Adjustment fields - updated field names
    has_adjustment = models.CharField(max_length=10, choices=HAS_ADJUSTMENT_CHOICES, default='ندارد', verbose_name="افزایش 25 درصدی قرار داد")
    adjustment_coefficient = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, verbose_name="درصد افزایش مبلغ قرار داد")
    
    # 25% Increase fields
    has_25_percent_increase = models.CharField(
        max_length=10, 
        choices=HAS_25_PERCENT_INCREASE_CHOICES, 
        default='ندارد', 
        verbose_name="25 درصد افزایش پیمان"
    )
    increase_coefficient_25_percent = models.DecimalField(
        max_digits=10, 
        decimal_places=4, 
        null=True, 
        blank=True, 
        default=1.0, # Default to 1, meaning no change unless specified
        verbose_name="ضریب 25 درصد افزایش پیمان"
    )
    
    # Contract information
    contract_start_date = models.DateField(null=True, blank=True)
    contract_end_date = models.DateField(null=True, blank=True)
    contract_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name="مبلغ قرارداد ( ریال)")    
    contract_type = models.CharField(max_length=50, choices=CONTRACT_TYPE_CHOICES, null=True, blank=True)
    execution_method = models.CharField(max_length=50, choices=EXECUTION_METHOD_CHOICES, null=True, blank=True)
    
    # Contractor information
    contractor_name = models.CharField(max_length=255, null=True, blank=True, verbose_name="نام پیمانکار")
    contractor_id = models.CharField(max_length=50, null=True, blank=True, verbose_name="شناسه پیمانکار")
    
    # New Financial Fields
    total_payments = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="مبلغ پرداختی زیر پروژه")
    total_prepayments = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="جمع مبلغ های پیش پرداخت")
    situation_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="مبلغ صورت وضعیت")
    total_adjustment_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="جمع مبلغ صورت وضعیت تعدیل")
    predicted_adjustment_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="مجموع مبلغ پیشبینی شده ی تعدیل های تا انتهای پروژه")
    
    # Keep subproject_debt as a regular field for now until migrations are fixed
    subproject_debt = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="دیون زیرپروژه")
    
    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_subprojects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # New field for transaction threshold
    transaction_threshold = models.CharField(max_length=10, choices=TRANSACTION_THRESHOLD_CHOICES, default='کوچک', verbose_name="نصاب معاملات")
    
    # Tender type
    tender_type = models.CharField(max_length=50, choices=TENDER_TYPE_CHOICES, null=True, blank=True, verbose_name="نوع مناقصه")
    
    # Has consultant choices
    has_consultant = models.CharField(max_length=10, choices=HAS_CONSULTANT_CHOICES, default='ندارد', verbose_name="مشاور")
    consultant_name = models.CharField(max_length=255, null=True, blank=True, verbose_name="نام مشاور")
    consultant_national_id = models.CharField(max_length=20, null=True, blank=True, verbose_name="شناسه ملی مشاور")
    
    class Meta:
        verbose_name = "زیرپروژه"
        verbose_name_plural = "زیرپروژه‌ها"
        ordering = ['project', 'sub_project_number']
    
    def __str__(self):
        if self.name:
            return f"{self.name} - {self.project.name} - {self.sub_project_type} ({self.sub_project_number})"
        return f"{self.project.name} - {self.sub_project_type} ({self.sub_project_number})"
    
    def get_total_allocation(self):
        """Returns the total sum of all allocations for this subproject"""
        return self.situation_reports.aggregate(Sum('amount'))['amount__sum'] or 0
    
    def get_cash_allocations(self):
        """Returns allocations of type 'تخصیص نقدی'"""
        return self.situation_reports.filter(allocation_type='تخصیص نقدی')
    
    def get_treasury_allocations(self):
        """Returns allocations of type 'تخصیص اسناد خزانه'"""
        return self.situation_reports.filter(allocation_type='تخصیص اسناد خزانه')
    
    def get_charity_allocations(self):
        """Returns allocations of type 'کمک خیرین'"""
        return self.situation_reports.filter(allocation_type='کمک خیرین')
    
    def get_travel_allocations(self):
        """Returns allocations of type 'مصوبات سفر'"""
        return self.situation_reports.filter(allocation_type='مصوبات سفر')
    
    def get_total_cash_allocation(self):
        """Returns the total amount of cash allocations"""
        result = self.get_cash_allocations().aggregate(Sum('amount'))['amount__sum']
        return result if result else 0
    
    def get_total_treasury_allocation(self):
        """Returns the total amount of treasury document allocations"""
        result = self.get_treasury_allocations().aggregate(Sum('amount'))['amount__sum']
        return result if result else 0
    
    def get_total_charity_allocation(self):
        """Returns the total amount of charity contributions"""
        result = self.get_charity_allocations().aggregate(Sum('amount'))['amount__sum']
        return result if result else 0
    
    def get_total_travel_allocation(self):
        """Returns the total amount of travel decree allocations"""
        result = self.get_travel_allocations().aggregate(Sum('amount'))['amount__sum']
        return result if result else 0
    
    def add_allocation(self, amount, letter_number, allocation_type, allocation_date=None, description=''):
        """
        Add a new allocation to this subproject
        
        Args:
            amount: The allocation amount
            letter_number: Reference letter number
            allocation_type: Type of allocation
            allocation_date: Date of allocation (defaults to today)
            description: Optional description
        
        Returns:
            The created SituationReport object
        """
        if allocation_date is None:
            allocation_date = timezone.now().date()
            
        return SituationReport.objects.create(
            sub_project=self,
            amount=amount,
            letter_number=letter_number,
            allocation_type=allocation_type,
            allocation_date=allocation_date,
            description=description
        )
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_state = None
        
        # Get the original state if this is not a new subproject
        if not is_new:
            try:
                old_instance = SubProject.objects.get(pk=self.pk)
                old_state = old_instance.state
                
            except SubProject.DoesNotExist:
                pass
        
        # Calculate dates based on rules
        self.calculate_dates()
        
        # Set the subproject_debt field value from the property method
        # to ensure consistency between the field and property
        self.subproject_debt = self.subproject_debts
        
        # Save the instance
        super().save(*args, **kwargs)
        
        # Update parent project's physical progress and overall status
        if hasattr(self, 'project') and self.project:
            self.project.physical_progress = self.project.calculate_physical_progress()
            
            # Only recalculate overall_status if state has changed
            if is_new or old_state != self.state:
                self.project.overall_status = self.project.calculate_overall_status()
            
            self.project.save(update_fields=['physical_progress', 'overall_status'])
    
    def calculate_financial_metrics(self):
        """
        Calculate the financial metrics.
        This method no longer sets properties directly since they are computed properties.
        """
        # The property methods will handle all calculations automatically
        # We don't need to set anything here since we're using property getters
        
        # For the subproject_debt field that might still exist in some installations
        # we can update it for backwards compatibility
        has_contract = self.contract_amount is not None
        
        # Calculate the values but don't try to set them as properties
        if hasattr(self, 'subproject_debt'):
            if has_contract:
                # Get the final contract amount
                final_amount = self.final_contract_amount
                # Calculate debt
                self.subproject_debt = final_amount + self.total_adjustment_amount - self.total_payments
            else:
                # For subprojects without contracts, set value to 0
                self.subproject_debt = 0
        
        # Make sure total_payments and total_adjustment_amount are set correctly
        # These are the actual database fields used by the property methods
        if self.total_payments is None:
            self.total_payments = 0
        
        if self.total_adjustment_amount is None:
            self.total_adjustment_amount = 0
    
    def calculate_dates(self):
        """
        Calculate start_date and end_date based on contract or relationship rules.
        """
        # 1. If contract dates exist, use them for subproject dates
        if self.contract_start_date and self.contract_end_date:
            self.start_date = self.contract_start_date
            self.end_date = self.contract_end_date
            return

        # 2. If there's a related subproject with relationship type, calculate dates based on that
        if self.related_subproject and self.relationship_type:
            # Get the related subproject's dates
            related_start = self.related_subproject.start_date
            related_end = self.related_subproject.end_date
            
            # Ensure the related subproject has valid dates before proceeding
            if not related_start or not related_end:
                return
            
            # Calculate delay days (default to 0 if not specified)
            delay_days = self.relationship_delay or 0
            
            # Calculate duration days from completion_percent
            duration_days = self.imagenary_duration or 30  # Default to 30 days if not set
            
            # Calculate dates based on relationship type
            if self.relationship_type == 'بعد از':  # After
                # Start AFTER the related project ENDS (+ delay)
                self.start_date = related_end + datetime.timedelta(days=delay_days)
                self.end_date = self.start_date + datetime.timedelta(days=duration_days)
                
            elif self.relationship_type == 'قبل از':  # Before
                # End BEFORE the related project STARTS (- delay)
                self.end_date = related_start - datetime.timedelta(days=delay_days)
                self.start_date = self.end_date - datetime.timedelta(days=duration_days)
                
            elif self.relationship_type == 'شروع با':  # Start With
                # Start WITH the related project START (+ delay)
                self.start_date = related_start + datetime.timedelta(days=delay_days)
                self.end_date = self.start_date + datetime.timedelta(days=duration_days)
                
            elif self.relationship_type == 'پایان با':  # End With
                # End WITH the related project END (+ delay)
                self.end_date = related_end + datetime.timedelta(days=delay_days)
                self.start_date = self.end_date - datetime.timedelta(days=duration_days)
    
    @property
    def latest_situation_report(self):
        """Returns the situation report with the highest report number for this subproject"""
        # Check both relationship fields (old and new) to find the latest report
        latest_report = SituationReport.objects.filter(
            Q(subproject=self)
        ).order_by('-allocation_date', '-report_number').first()
        
        return latest_report
    
    @property
    def latest_adjustment_report(self):
        """Returns the adjustment situation report with the highest report number for this subproject"""
        latest_report = AdjustmentSituationReport.objects.filter(
            subproject=self
        ).order_by('-allocation_date', '-report_number').first()
        
        return latest_report
    
    @property
    def final_contract_amount(self):
        """
        Calculate the final contract amount based on the base contract amount and any adjustments
        """
        if not self.contract_amount:
            return self.imagenrary_cost or 0
            
        # Base contract amount
        base_amount = self.contract_amount

        # Apply adjustment increase if it exists (as percentage)
        if self.has_adjustment == 'دارد' and self.adjustment_coefficient:
            # Convert percentage to decimal (e.g. 25% becomes 0.25)
            adjustment_decimal = self.adjustment_coefficient / 100
            base_amount = base_amount * (1 + adjustment_decimal)
            
        # For backwards compatibility, also check the 25% increase field
        if self.has_25_percent_increase == 'دارد' and self.increase_coefficient_25_percent:
            base_amount = base_amount * self.increase_coefficient_25_percent

        return base_amount
    
    @property
    def total_latest_payments_sum(self):
        """
        Returns the sum of the latest situation payment and the latest adjustment payment
        """
        situation_payment = Decimal(str(self.latest_situation_payment or '0'))
        adjustment_payment = Decimal(str(self.latest_adjustment_payment or '0'))
        return situation_payment + adjustment_payment
    
    @property
    def total_latest_payment(self):
        """
        Calculate the total payment by summing:
        1. Payment from the latest regular situation report
        2. Payment from the latest adjustment situation report
        """
        total_payment = 0
        
        # Get the latest regular situation report
        latest_report = self.latest_situation_report
        if latest_report and hasattr(latest_report, 'payment_amount'):
            total_payment += float(latest_report.payment_amount)
        
        # Get the latest adjustment situation report
        latest_adjustment = self.latest_adjustment_report
        if latest_adjustment and hasattr(latest_adjustment, 'payment_amount'):
            total_payment += float(latest_adjustment.payment_amount)
            
        return total_payment

    @property
    def latest_situation_payment(self):
        """
        Returns the payment amount of the latest situation report
        """
        latest_report = self.latest_situation_report
        if latest_report and hasattr(latest_report, 'payment_amount'):
            return latest_report.payment_amount
        return 0
        
    @property
    def latest_adjustment_payment(self):
        """
        Returns the payment amount of the latest adjustment report
        """
        latest_adjustment = self.latest_adjustment_report
        if latest_adjustment and hasattr(latest_adjustment, 'payment_amount'):
            return latest_adjustment.payment_amount
        return 0

    @property
    def subproject_debts(self):
        """
        دیون زیرپروِژه
        For subprojects with contract: جمع مبلغ های پیش پرداخت + مبلغ صورت وضعیت + جمع مبلغ صورت وضعیت تعدیل - جمع مبلغ پرداخت ها
        For subprojects without contract: 0
        """
        if not self.contract_amount:
            return Decimal('0')
            
        # Get advance payments amount
        advance_payments = self.total_advance_payments or Decimal('0')
        
        # Get situation report amount
        situation_amount = self.situation_report_amount or Decimal('0')
        
        # Get total adjustment reports amount
        adjustment_amount = self.total_adjustment_reports or Decimal('0')
        
        # Get total payments amount
        total_payments = self.total_payment_amount or Decimal('0')
        
        # Calculate debt: advance_payments + situation_amount + adjustment_amount - total_payments
        debt = advance_payments + situation_amount + adjustment_amount - total_payments
        
        # Debt should not be negative
        return max(debt, Decimal('0'))
    
    @property
    def financial_progress_amount(self):
        """
        مبلغ پیشرفت مالی زیرپروژه
        Calculated as: مبلغ پرداختی زیر پروژه - جمع مبلغ صورت وضعیت تعدیل
        """
        total_payment = self.total_payments or Decimal('0')
        total_adjustment = self.total_adjustment_amount or Decimal('0')
        
        return max(total_payment - total_adjustment, Decimal('0'))
    
    @property
    def financial_progress_percentage(self):
        """
        پیشرفت مالی زیرپروژه
        For subprojects with contract: مبلغ پیشرفت مالی زیرپروژه / مبلغ نهایی قرارداد * 100
        For subprojects without contract: 0
        """
        if not self.contract_amount:
            return Decimal('0')
            
        final_amount = self.final_contract_amount
        if final_amount <= 0:
            return Decimal('0')
            
        progress_amount = self.financial_progress_amount
        
        # Calculate percentage and round to 2 decimal places
        percentage = (progress_amount / final_amount) * 100
        return min(Decimal('100'), round(percentage, 2))
    
    def calculate_subproject_debts(self):
        """
        Calculate the subproject debts (replaces the old calculate_debt method)
        دیون زیرپروِژه
        """
        # For subprojects without contract, debt is 0
        if not self.contract_amount:
            return Decimal('0')
            
        # Get the final contract amount
        final_amount = self.final_contract_amount
        
        # Use Decimal for precise calculation
        final_amount = Decimal(str(final_amount))
        
        # Get total payments
        total_payment = Decimal(str(self.total_payments or '0'))
        
        # Get total adjustment amount
        total_adjustment = Decimal(str(self.total_adjustment_amount or '0'))
        
        # Calculate debt: final_contract_amount + total_adjustment_amount - total_payments
        debt = final_amount + total_adjustment - total_payment
        
        # Debt should not be negative
        if debt < 0:
            debt = Decimal('0')
                
        return debt

    @property
    def total_payments(self):
        """Returns the total amount of payments for this subproject."""
        return self.payments.aggregate(Sum('amount'))['amount__sum'] or 0

    @property
    def total_advance_payments(self):
        """Returns the total amount of advance payments for this subproject."""
        return self.financial_documents.filter(
            document_type='advance_payment'
        ).aggregate(Sum('approved_amount'))['approved_amount__sum'] or 0

    @property
    def situation_report_amount(self):
        """
        Returns the amount of the latest permanent or temporary situation report.
        If a permanent report exists, use that, otherwise use the latest temporary report.
        """
        permanent_report = self.financial_documents.filter(
            document_type='permanent_report'
        ).order_by('-document_number').first()
        
        if permanent_report:
            return permanent_report.approved_amount
        
        # If no permanent report, use the latest temporary report
        temporary_report = self.financial_documents.filter(
            document_type='temporary_report'
        ).order_by('-document_number').first()
        
        return temporary_report.approved_amount if temporary_report else 0

    @property
    def total_adjustment_reports(self):
        """Calculate total adjustment reports amount from FinancialDocument model"""
        return self.financial_documents.filter(
            document_type='adjustment_report'
        ).aggregate(total=Sum('approved_amount'))['total'] or 0

    @property
    def total_payment_amount(self):
        """Calculate total payment amount from Payment model"""
        return self.payments.aggregate(
            total=Sum('amount')
        )['total'] or 0

    @property
    def required_credit_for_contract_completion(self):
        """
        اعتبار مورد نیاز تکمیل قرار داد
        Calculate required credit for contract completion:
        مبلغ نهایی قرارداد + جمع مبلغ صورت وضعیت تعدیل + مجموع مبلغ پیشبینی شده ی تعدیل های تا انتهای پروژه - جمع مبلغ پرداخت ها
        """
        # Get final contract amount
        final_contract_amount = self.final_contract_amount or Decimal('0')
        
        # Get total adjustment reports amount
        total_adjustment_reports = self.total_adjustment_reports or Decimal('0')
        
        # Get predicted adjustment amount
        predicted_adjustment = self.predicted_adjustment_amount or Decimal('0')
        
        # Get total payments amount
        total_payments = self.total_payment_amount or Decimal('0')
        
        # Calculate required credit
        required_credit = final_contract_amount + total_adjustment_reports + predicted_adjustment - total_payments
        
        # Return the result (can be negative if overpaid)
        return required_credit


class SituationReport(models.Model):
    TYPE_CHOICES = [
        ('موقت', 'موقت'),
        ('دائم', 'دائم'),
    ]
    
    # Main field for linking to SubProject
    subproject = models.ForeignKey(
        'SubProject', 
        on_delete=models.CASCADE, 
        related_name='situation_reports',
        verbose_name='زیرپروژه'
    )
    
    report_number = models.PositiveIntegerField(verbose_name="شماره صورت وضعیت", blank=True, null=True)
    allocation_type = models.CharField(max_length=50, choices=TYPE_CHOICES, verbose_name="نوع صورت وضعیت")
    allocation_date = models.DateField(verbose_name="تاریخ صورت وضعیت")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")
    
    # Direct payment amount field
    payment_amount_field = models.BigIntegerField(verbose_name="مبلغ پرداختی")
    
    created_at = models.DateTimeField(default=timezone.now, verbose_name="تاریخ ایجاد")
    
    class Meta:
        verbose_name = "صورت وضعیت ها کارکرد"
        verbose_name_plural = "صورت وضعیت‌ها کارکرد"
        ordering = ['-allocation_date']
    
    def __str__(self):
        return f"{self.subproject} - {self.allocation_type} - {self.payment_amount_field:,} ریال"
        
    @property
    def payment_amount(self):
        """
        Return the direct payment amount
        """
        return self.payment_amount_field
        
    @property
    def jalali_allocation_date(self):
        """Convert Gregorian date to Jalali format for display"""
        if self.allocation_date:
            return gregorian_to_jalali(self.allocation_date)
        return None
        
    def save(self, *args, **kwargs):
        # Auto-increment report number if not provided
        if not self.report_number and self.subproject:
            # Get the highest report number for this subproject
            max_report_number = SituationReport.objects.filter(
                subproject=self.subproject
            ).aggregate(models.Max('report_number'))['report_number__max'] or 0
            # Increment by 1
            self.report_number = max_report_number + 1
        
        super().save(*args, **kwargs)


class AdjustmentSituationReport(models.Model):
    TYPE_CHOICES = [
        ('موقت', 'موقت'),
        ('دائم', 'دائم'),
    ]
    
    # Main field linking to SubProject
    subproject = models.ForeignKey(
        'SubProject', 
        on_delete=models.CASCADE, 
        related_name='adjustment_situation_reports',
        verbose_name='زیرپروژه'
    )
    
    report_number = models.PositiveIntegerField(verbose_name="شماره صورت وضعیت تعدیل", blank=True, null=True)
    allocation_date = models.DateField(verbose_name="تاریخ صورت وضعیت تعدیل")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")
    
    # Direct payment amount field for adjustment
    payment_amount_field = models.BigIntegerField(verbose_name="مبلغ پرداختی تعدیل")
    
    created_at = models.DateTimeField(default=timezone.now, verbose_name="تاریخ ایجاد")
    
    class Meta:
        verbose_name = "صورت وضعیت ها تعدیل"
        verbose_name_plural = "صورت وضعیت‌ها تعدیل"
        ordering = ['-allocation_date']
    
    def __str__(self):
        return f"{self.subproject} - تعدیل - {self.payment_amount_field:,} ریال"
        
    @property
    def payment_amount(self):
        """
        Return the direct payment amount
        """
        return self.payment_amount_field
        
    @property
    def jalali_allocation_date(self):
        """Convert Gregorian date to Jalali format for display"""
        if self.allocation_date:
            return gregorian_to_jalali(self.allocation_date)
        return None
        
    def save(self, *args, **kwargs):
        # Auto-increment report number if not provided
        if not self.report_number and self.subproject:
            # Get the highest report number for this subproject
            max_report_number = AdjustmentSituationReport.objects.filter(
                subproject=self.subproject
            ).aggregate(models.Max('report_number'))['report_number__max'] or 0
            # Increment by 1
            self.report_number = max_report_number + 1
        
        super().save(*args, **kwargs)


class SubProjectUpdateHistory(models.Model):
    """Model to track subproject update history."""
    subproject = models.ForeignKey(SubProject, on_delete=models.CASCADE, related_name='update_history')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subproject_updates')
    updated_at = models.DateTimeField(auto_now_add=True)
    field_name = models.CharField(max_length=50)
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "تاریخچه بروزرسانی زیرپروژه"
        verbose_name_plural = "تاریخچه بروزرسانی زیرپروژه‌ها"
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.subproject} - {self.field_name} changed by {self.updated_by.username}"


@receiver(pre_save, sender=SubProject)
def track_subproject_changes(sender, instance, **kwargs):
    """Track changes to subproject fields for update history."""
    # Skip for new instances
    if instance.pk is None:
        return
    
    try:
        old_instance = SubProject.objects.get(pk=instance.pk)
    except SubProject.DoesNotExist:
        return
            
    # Fields to track
    fields_to_track = [
        'sub_project_type', 'state', 'physical_progress',
        'remaining_work', 'contract_start_date', 'contract_end_date', 
        'contract_amount', 'contract_type', 'execution_method', 
        'has_adjustment', 'adjustment_coefficient', 'start_date', 'end_date',
        'imagenary_duration', 'relationship_delay', 'relationship_type', 'related_subproject_id'
    ]
    
    updates = []
    for field in fields_to_track:
        old_value = getattr(old_instance, field)
        new_value = getattr(instance, field)
        
        # Handle None values for comparison
        if old_value != new_value:
            updates.append({
                'field_name': field,
                'old_value': str(old_value) if old_value is not None else '',
                'new_value': str(new_value) if new_value is not None else ''
            })
    
    # Store updates in instance._updates for post_save handler
    instance._updates = updates
        

@receiver(post_save, sender=SubProject)
def save_subproject_updates(sender, instance, created, **kwargs):
    """Save tracked changes to the update history."""
    if created:
        return  # Skip for new instances
    
    if not hasattr(instance, '_updates'):
        return
    
    updates = instance._updates
    if not updates:
        return
        
    # Get the current user from thread local storage
    user = getattr(instance, '_current_user', None)
    if user is None:
        return
        
    # Create history entries
    for update in updates:
            SubProjectUpdateHistory.objects.create(
                subproject=instance,
                updated_by=user,
            field_name=update['field_name'],
            old_value=update['old_value'],
            new_value=update['new_value']
        )
            
    # Update parent project's physical progress if physical_progress was updated
    for update in updates:
        if update['field_name'] == 'physical_progress' or update['field_name'] == 'contract_amount' or update['field_name'] == 'adjustment_coefficient':
            # Update the parent project's physical progress
            project = instance.project
            project.physical_progress = project.calculate_physical_progress()
            project.save(update_fields=['physical_progress'])
            break


class SubProjectRejectionComment(models.Model):
    subproject = models.ForeignKey(SubProject, on_delete=models.CASCADE, related_name='rejection_comments')
    expert = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='subproject_rejection_comments')
    field_name = models.CharField(max_length=100)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "نظر رد زیرپروژه"
        verbose_name_plural = "نظرات رد زیرپروژه"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.subproject} - {self.field_name} - {self.expert.get_full_name()}"


class ProjectSituation(models.Model):
    """Model for tracking project situation reports"""
    
    TYPE_CHOICES = [
        ('مالی', 'مالی'),
        ('فیزیکی', 'فیزیکی'),
        ('حقوقی', 'حقوقی'),
        ('فنی', 'فنی'),
    ]
    
    project = models.ForeignKey('creator_project.Project', on_delete=models.CASCADE, related_name='situations', verbose_name="پروژه")
    situation_type = models.CharField(max_length=50, choices=TYPE_CHOICES, verbose_name="نوع وضعیت")
    description = models.TextField(verbose_name="توضیحات")
    report_date = models.DateField(verbose_name="تاریخ گزارش")
    is_resolved = models.BooleanField(default=False, verbose_name="حل شده")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reported_situations')
    created_at = models.DateTimeField(default=timezone.now, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")
    
    class Meta:
        verbose_name = "وضعیت پروژه"
        verbose_name_plural = "وضعیت های پروژه"
        ordering = ['-report_date']
    
    def __str__(self):
        return f"{self.project.name} - {self.situation_type} - {self.report_date}"


# Add a post_save signal to SubProject model
@receiver(post_save, sender=SubProject)
def clear_rejection_comments_on_draft(sender, instance, **kwargs):
    """
    Clear rejection comments when parent project status changes to draft
    """
    # Check parent project status instead
    if instance.project and not instance.project.is_submitted:
        # If parent project is in draft, delete all rejection comments for this subproject
        SubProjectRejectionComment.objects.filter(subproject=instance).delete()


# Signals to reset SubProject approval status when SituationReport changes
@receiver(post_save, sender=SituationReport)
def reset_subproject_status_on_save(sender, instance, **kwargs):
    """Updates the parent project when a SituationReport is saved."""
    # Safely check if the instance has the required attributes
    if hasattr(instance, 'subproject') and instance.subproject is not None:
        subproject = instance.subproject
    elif hasattr(instance, 'sub_project') and instance.sub_project is not None:
        subproject = instance.sub_project
    else:
        # No subproject relationship found, exit early
        return
        
    # Only continue if we found a valid subproject
    if subproject and subproject.project:
        # Update the parent project's physical progress
        project = subproject.project
        project.physical_progress = project.calculate_physical_progress()
        project.save(update_fields=['physical_progress'])
        print(f"DEBUG: Updated progress for Project {project.id} due to SituationReport save.")

@receiver(post_delete, sender=SituationReport)
def reset_subproject_status_on_delete(sender, instance, **kwargs):
    """Updates the parent project when a SituationReport is deleted."""
    # Safely check if the instance has the required attributes
    if hasattr(instance, 'subproject') and instance.subproject is not None:
        subproject = instance.subproject
    elif hasattr(instance, 'sub_project') and instance.sub_project is not None:
        subproject = instance.sub_project
    else:
        # No subproject relationship found, exit early
        return
        
    # Only continue if we found a valid subproject
    if subproject and subproject.project:
        # Update the parent project's physical progress
        project = subproject.project
        project.physical_progress = project.calculate_physical_progress()
        project.save(update_fields=['physical_progress'])
        print(f"DEBUG: Updated progress for Project {project.id} due to SituationReport delete.")

@receiver(post_save, sender=SituationReport)
@receiver(post_save, sender=AdjustmentSituationReport)
def update_subproject_financial_fields(sender, instance, **kwargs):
    """Updates the related SubProject when a payment report is saved."""
    # Get the related subproject
    if hasattr(instance, 'subproject') and instance.subproject is not None:
        subproject = instance.subproject
        
        # Recalculate financial fields - will be handled by property getters
        # Just make sure the base fields are updated
        if sender == SituationReport:
            payments = SituationReport.objects.filter(subproject=subproject).aggregate(Sum('payment_amount_field'))
            subproject.total_payments = payments['payment_amount_field__sum'] or 0
        elif sender == AdjustmentSituationReport:
            adjustments = AdjustmentSituationReport.objects.filter(subproject=subproject).aggregate(Sum('payment_amount_field'))
            subproject.total_adjustment_amount = adjustments['payment_amount_field__sum'] or 0
            
        # Save with update_fields to avoid recursive saves
        update_fields = ['total_payments', 'total_adjustment_amount']
        if hasattr(subproject, 'subproject_debt'):
            update_fields.append('subproject_debt')
            
        subproject.save(update_fields=update_fields)

@receiver(post_delete, sender=SituationReport)
@receiver(post_delete, sender=AdjustmentSituationReport)
def update_subproject_financial_fields_on_delete(sender, instance, **kwargs):
    """Updates the related SubProject when a payment report is deleted."""
    # Get the related subproject
    if hasattr(instance, 'subproject') and instance.subproject is not None:
        subproject = instance.subproject
        
        # Recalculate financial fields - will be handled by property getters
        # Just make sure the base fields are updated
        if sender == SituationReport:
            payments = SituationReport.objects.filter(subproject=subproject).aggregate(Sum('payment_amount_field'))
            subproject.total_payments = payments['payment_amount_field__sum'] or 0
        elif sender == AdjustmentSituationReport:
            adjustments = AdjustmentSituationReport.objects.filter(subproject=subproject).aggregate(Sum('payment_amount_field'))
            subproject.total_adjustment_amount = adjustments['payment_amount_field__sum'] or 0
            
        # Save with update_fields to avoid recursive saves
        update_fields = ['total_payments', 'total_adjustment_amount']
        if hasattr(subproject, 'subproject_debt'):
            update_fields.append('subproject_debt')
            
        subproject.save(update_fields=update_fields)

# Run this function once to update all subprojects with the correct values
def update_all_subproject_values():
    """Update values for all subprojects."""
    for subproject in SubProject.objects.all():
        # Calculate total payments
        payments = SituationReport.objects.filter(subproject=subproject).aggregate(Sum('payment_amount_field'))
        subproject.total_payments = payments['payment_amount_field__sum'] or 0
        
        # Calculate total adjustment amount
        adjustments = AdjustmentSituationReport.objects.filter(subproject=subproject).aggregate(Sum('payment_amount_field'))
        subproject.total_adjustment_amount = adjustments['payment_amount_field__sum'] or 0
        
        # Save the subproject with these updated values
        update_fields = ['total_payments', 'total_adjustment_amount']
        if hasattr(subproject, 'subproject_debt'):
            update_fields.append('subproject_debt')
        subproject.save(update_fields=update_fields)

@receiver(post_save, sender=SubProject)
def update_dependent_subprojects(sender, instance, created, **kwargs):
    """Update related/dependent subprojects when a subproject is saved."""
    # Find all subprojects that have this one as related
    related_subprojects = SubProject.objects.filter(related_subproject=instance)
    
    # Update their dates based on relationship
    for related in related_subprojects:
        # This will trigger calculate_dates() in save()
        related.save(update_fields=['updated_at'])


class SubProjectGalleryImage(models.Model):
    """Model for storing gallery images for subprojects directly in database."""
    subproject = models.ForeignKey(SubProject, on_delete=models.CASCADE, related_name='gallery_images')
    
    # Replace ImageField with BinaryField
    image = models.BinaryField(verbose_name="تصویر")
    
    # Optional: Add mime type to help with image rendering
    image_mime_type = models.CharField(max_length=100, default='image/jpeg')
    
    title = models.CharField(max_length=255, blank=True, null=True, verbose_name="عنوان")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")
    upload_date = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ آپلود")
    
    class Meta:
        verbose_name = "تصویر گالری زیرپروژه"
        verbose_name_plural = "تصاویر گالری زیرپروژه"
        ordering = ['-upload_date']  # Newest images first
    
    def __str__(self):
        if self.title:
            return f"{self.title} - {self.subproject}"
        return f"تصویر {self.id} - {self.subproject}"


class FinancialDocument(models.Model):
    """
    Represents a financial document in the system.
    """
    subproject = models.ForeignKey('SubProject', on_delete=models.CASCADE, related_name='financial_documents')
    document_type = models.CharField(max_length=20, choices=FINANCIAL_DOCUMENT_TYPES, verbose_name=_('نوع سند مالی'))
    document_number = models.PositiveIntegerField(verbose_name=_('شماره سند مالی'), default=1)
    related_document = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, 
                                        related_name='related_documents', verbose_name=_('ارتباط با سند مالی'))
    contractor_amount = models.DecimalField(max_digits=14, decimal_places=0, verbose_name=_('مبلغ ناخالص پیمان کار'))
    contractor_date = models.DateField(verbose_name=_('تاریخ ارسال سند مالی پیمان کار'))
    contractor_submit_date = models.DateField(verbose_name=_('تاریخ ارسال سند مالی پیمان کار'))
    approved_amount = models.DecimalField(max_digits=14, decimal_places=0, verbose_name=_('مبلغ ناخالص تایید شده'))
    approval_date = models.DateField(null=True, blank=True, verbose_name=_('تاریخ تایید سند مالی'))
    description = models.TextField(blank=True, null=True, verbose_name=_('توضیحات'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_financial_documents', 
                                  null=True, blank=True)

    class Meta:
        verbose_name = _('سند مالی')
        verbose_name_plural = _('اسناد مالی')
        # Ensure document_number is unique per type per subproject
        unique_together = ('subproject', 'document_type', 'document_number')
        ordering = ['document_type', 'document_number']

    def __str__(self):
        return f"{self.get_document_type_display()} #{self.document_number} - {self.subproject}"

    def save(self, *args, **kwargs):
        # Auto-increment document_number if not provided or if it would cause a conflict
        if not self.document_number or self.pk is None:
            # Check if this combination already exists
            existing = FinancialDocument.objects.filter(
                subproject=self.subproject,
                document_type=self.document_type,
                document_number=self.document_number or 1
            ).exclude(pk=self.pk if self.pk else None).exists()
            
            if existing or not self.document_number:
                max_num = FinancialDocument.objects.filter(
                    subproject=self.subproject,
                    document_type=self.document_type
                ).aggregate(models.Max('document_number'))['document_number__max'] or 0
                self.document_number = max_num + 1
            
        # Ensure contractor_submit_date is set to the same value as contractor_date
        if self.contractor_date and not self.contractor_submit_date:
            self.contractor_submit_date = self.contractor_date
            
        # Ensure approval_date has a value (use contractor_date if not provided)
        if not self.approval_date:
            self.approval_date = self.contractor_date
            
        super().save(*args, **kwargs)

    @property
    def jalali_contractor_date(self):
        if self.contractor_date:
            return gregorian_to_jalali(self.contractor_date)
        return None

    @property
    def jalali_approval_date(self):
        if self.approval_date:
            return gregorian_to_jalali(self.approval_date)
        return None

class DocumentFile(models.Model):
    """
    Files attached to financial documents
    """
    document = models.ForeignKey(FinancialDocument, on_delete=models.CASCADE, related_name='documents')
    
    # Replace FileField with BinaryField
    file = models.BinaryField(verbose_name=_('فایل'))
    
    # Add mime type to help with file rendering
    file_mime_type = models.CharField(max_length=100, default='application/octet-stream', verbose_name=_("نوع فایل (MIME)"))
    
    filename = models.CharField(max_length=255, verbose_name=_('نام فایل'))
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'creator_subproject_documentfile'
    
    def __str__(self):
        return self.filename

    def get_absolute_url(self):
        from django.urls import reverse  # Moved import inside the method
        return reverse('creator_subproject:serve_document_file', args=[self.pk])

class Payment(models.Model):
    """
    Represents a payment record in the system.
    """
    subproject = models.ForeignKey('SubProject', on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=14, decimal_places=0, verbose_name=_('مبلغ پرداخت شده'))
    related_document = models.ForeignKey(FinancialDocument, on_delete=models.SET_NULL, 
                                        null=True, blank=True, related_name='payments',
                                        verbose_name=_('سند مالی مرتبط'))
    payment_date = models.DateField(verbose_name=_('تاریخ پرداختی'))
    description = models.TextField(blank=True, null=True, verbose_name=_('توضیحات'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_payments',
                                  null=True, blank=True)

    class Meta:
        verbose_name = _('پرداختی')
        verbose_name_plural = _('پرداختی ها')
        ordering = ['payment_date']

    def __str__(self):
        return f"پرداختی {self.amount} - {self.subproject}"

    @property
    def jalali_payment_date(self):
        if self.payment_date:
            return gregorian_to_jalali(self.payment_date)
        return None
