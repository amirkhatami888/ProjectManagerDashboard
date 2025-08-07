from django.db import models
from django.conf import settings
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone
import random
import json
import jdatetime
from datetime import datetime


def generate_unique_project_id():
    """Generate a unique 6-digit project ID not used by any existing project."""
    while True:
        project_id = str(random.randint(100000, 999999))
        if not Project.objects.filter(project_id=project_id).exists():
            return project_id


class Project(models.Model):
    # Changed to match SubProject's sub_project_type choices
    PROJECT_TYPE_CHOICES = [
        ('احداث', 'احداث'),
        ('تکمیل', 'تکمیل'),
        ('محوطه سازی', 'محوطه سازی'),
        ('دیوار کشی', 'دیوار کشی'),
        ('محوطه سازی و دیوار کشی', 'محوطه سازی و دیوار کشی'),
        ('تعمیرات', 'تعمیرات'),
        ('مشاور فاز یک و دو (طراحی)', 'مشاور فاز یک و دو (طراحی)'),
        ('مشاور فاز سه (نظارت)', 'مشاور فاز سه (نظارت)'),
    ]
    
    # Define province choices directly
    PROVINCE_CHOICES = [
        ('البرز', 'البرز'),
        ('آذربایجان شرقی', 'آذربایجان شرقی'),
        ('آذربایجان غربی', 'آذربایجان غربی'),
        ('بوشهر', 'بوشهر'),
        ('چهارمحال و بختیاری', 'چهارمحال و بختیاری'),
        ('فارس', 'فارس'),
        ('گیلان', 'گیلان'),
        ('گلستان', 'گلستان'),
        ('همدان', 'همدان'),
        ('هرمزگان', 'هرمزگان'),
        ('ایلام', 'ایلام'),
        ('اصفهان', 'اصفهان'),
        ('کرمان', 'کرمان'),
        ('کرمانشاه', 'کرمانشاه'),
        ('خراسان شمالی', 'خراسان شمالی'),
        ('خراسان رضوی', 'خراسان رضوی'),
        ('خراسان جنوبی', 'خراسان جنوبی'),
        ('خوزستان', 'خوزستان'),
        ('کهگیلویه و بویراحمد', 'کهگیلویه و بویراحمد'),
        ('کردستان', 'کردستان'),
        ('لرستان', 'لرستان'),
        ('مرکزی', 'مرکزی'),
        ('مازندران', 'مازندران'),
        ('قزوین', 'قزوین'),
        ('قم', 'قم'),
        ('سمنان', 'سمنان'),
        ('سیستان و بلوچستان', 'سیستان و بلوچستان'),
        ('تهران', 'تهران'),
        ('یزد', 'یزد'),
        ('زنجان', 'زنجان'),
        ('کیش', 'کیش'),
        ("اردبیل", "اردبیل"),
    ]
    
    # LICENSE_STATE_CHOICES moved to Program model
    
    OVERALL_STATUS_CHOICES = [
        ("فعال", "فعال"),
        ("تامین اعتبار", "تامین اعتبار"),
        ("غیره فعال", "غیره فعال"),
    ]
    
    # Information part
    # Add foreign key to Program
    program = models.ForeignKey('creator_program.Program', on_delete=models.CASCADE, related_name='projects', verbose_name="طرح", null=True, blank=True)
    name = models.CharField(max_length=255)
    project_id = models.CharField(max_length=50, unique=True, blank=True)  # Will be auto-generated
    project_type = models.CharField(max_length=50, choices=PROJECT_TYPE_CHOICES, verbose_name="نوع پروژه")
    province = models.CharField(max_length=50, choices=PROVINCE_CHOICES)
    city = models.CharField(max_length=50)
    # Removed longitude and latitude fields - moved to Program model
    area_size = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="عرصه")
    site_area = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="مساحت محوطه سازی")
    wall_length = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="طول دیوار کشی")
    notables = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="اعیان")
    floor = models.IntegerField(blank=True, null=True, verbose_name="طبقه")
    # Removed license_state and license_code fields - moved to Program model
    physical_progress = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    estimated_opening_time = models.DateField(null=True, blank=True, verbose_name="تاریخ پایان پروژه")
    overall_status = models.CharField(max_length=50, choices=OVERALL_STATUS_CHOICES, default="غیره فعال", verbose_name="وضعیت کلی")

    # Financial part
    allocation_credit_cash_national = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    allocation_credit_cash_province = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    allocation_credit_cash_charity = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    allocation_credit_cash_travel = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    
    allocation_credit_treasury_national = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    allocation_credit_treasury_province = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    allocation_credit_treasury_travel = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    
    debt = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Cached financial calculations
    cached_total_debt = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="مجموع دیون")
    cached_required_credit_contracts = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="اعتبار مورد نیاز تکمیل قرار داد ها")
    cached_required_credit_project = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="اعتبار مورد نیاز تکمیل پروژه")
    
    # Subproject slots
    max_subprojects = 10  # Reserved space for 10 subprojects
    
    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_projects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_approved = models.BooleanField(default=False)
    is_submitted = models.BooleanField(default=False, verbose_name="ارسال شده")
    is_expert_approved = models.BooleanField(default=False, verbose_name="تایید کارشناس")
    
    class Meta:
        verbose_name = "پروژه"
        verbose_name_plural = "پروژه‌ها"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.project_id})"
    
    def get_subproject_count(self):
        """Returns the current number of subprojects."""
        return self.subprojects.count()
    
    def has_available_subproject_slots(self):
        """Checks if there are available slots for new subprojects."""
        return self.get_subproject_count() < self.max_subprojects
    
    def get_subproject_by_index(self, index):
        """Get a subproject by its index (0-9)."""
        if 0 <= index < self.max_subprojects:
            subprojects = list(self.subprojects.all().order_by('id')[:self.max_subprojects])
            if index < len(subprojects):
                return subprojects[index]
        return None
    
    def get_subproject_by_number(self, number):
        """Get a subproject by its sub_project_number."""
        try:
            return self.subprojects.get(sub_project_number=number)
        except:
            return None
    
    def get_available_subproject_slots(self):
        """Returns the number of available subproject slots."""
        return self.max_subprojects - self.get_subproject_count()
    
    def get_all_subprojects(self):
        """Returns all subprojects (limited to max_subprojects)."""
        return self.subprojects.all().order_by('id')[:self.max_subprojects]
    
    def get_next_subproject_number(self):
        """Returns the next available subproject number."""
        existing_numbers = set(self.subprojects.values_list('sub_project_number', flat=True))
        for i in range(1, self.max_subprojects + 1):
            if i not in existing_numbers:
                return i
        return None
    
    def create_subproject(self, sub_project_type, start_date, state, remaining_work, 
                         estimated_opening_time, contract_start_date, contract_end_date, contract_amount,
                         contract_type, execution_method, is_suportting_charity='ندارد', user=None):
        """
        Create a new subproject for this project.
        
        Args:
            sub_project_type: Type of subproject
            start_date: Start date
            state: State of subproject
            remaining_work: Remaining work description
            estimated_opening_time: Estimated opening date
            contract_start_date: Contract start date
            contract_end_date: Contract end date
            contract_amount: Contract amount
            contract_type: Contract type
            execution_method: Execution method
            is_suportting_charity: Whether charity is supporting (default: 'ندارد')
            user: User creating this subproject (default: project creator)
            
        Returns:
            The created SubProject instance, or None if max subproject limit reached
        """
        from creator_subproject.models import SubProject
        
        # Check if we've reached the max number of subprojects
        if not self.has_available_subproject_slots():
            return None
        
        # Get the next available subproject number
        sub_project_number = self.get_next_subproject_number()
        if sub_project_number is None:
            return None
        
        # Use the project creator if no user is specified
        if user is None:
            user = self.created_by
        
        # Create the new subproject
        subproject = SubProject.objects.create(
            project=self,
            sub_project_type=sub_project_type,
            sub_project_number=sub_project_number,
            start_date=start_date,
            state=state,
            remaining_work=remaining_work,
            estimated_opening_time=estimated_opening_time,
            contract_start_date=contract_start_date,
            contract_end_date=contract_end_date,
            contract_amount=contract_amount,
            contract_type=contract_type,
            execution_method=execution_method,
            is_suportting_charity=is_suportting_charity,
            created_by=user,
            physical_progress=0
        )
        
        return subproject
    
    def add_allocation_to_subproject(self, sub_project_number, amount, letter_number, allocation_type, 
                                     allocation_date=None, description=''):
        """
        Add a financial allocation to a subproject.
        
        Args:
            sub_project_number: The subproject number
            amount: Allocation amount
            letter_number: Reference letter number
            allocation_type: Type of allocation
            allocation_date: Date of allocation (defaults to today)
            description: Optional description
            
        Returns:
            The created AllocationFinance object or None if subproject not found
        """
        subproject = self.get_subproject_by_number(sub_project_number)
        if subproject:
            return subproject.add_allocation(
                amount=amount,
                letter_number=letter_number,
                allocation_type=allocation_type,
                allocation_date=allocation_date,
                description=description
            )
        return None
    
    def get_total_allocation(self):
        """Returns the total allocation amount for this project."""
        allocations = self.allocations.all()
        total = sum(allocation.amount for allocation in allocations)
        return total
        
    def get_total_allocation_by_type(self, allocation_type):
        """Returns the total allocation amount for this project by allocation type."""
        allocations = self.allocations.filter(allocation_type=allocation_type)
        total = sum(allocation.amount for allocation in allocations)
        return total
    
    def get_total_cash_national(self):
        """Returns the total cash national allocation."""
        return self.get_total_allocation_by_type('اعتبار نقدی-ملی')
        
    def get_total_cash_provincial(self):
        """Returns the total cash provincial allocation."""
        return self.get_total_allocation_by_type('اعتبار نقدی-استانی')
        
    def get_total_cash_travel(self):
        """Returns the total cash travel allocation."""
        return self.get_total_allocation_by_type('اعتبار نقدی-سفر')
        
    def get_total_treasury_national(self):
        """Returns the total treasury national allocation."""
        return self.get_total_allocation_by_type('اعتبار اسناد خزانه-ملی')
        
    def get_total_treasury_provincial(self):
        """Returns the total treasury provincial allocation."""
        return self.get_total_allocation_by_type('اعتبار اسناد خزانه-استانی')
        
    def get_total_treasury_travel(self):
        """Returns the total treasury travel allocation."""
        return self.get_total_allocation_by_type('اعتبار اسناد خزانه-سفر')
    
    def get_total_cash_charity(self):
        """Returns the total cash charity allocation."""
        return self.get_total_allocation_by_type('نقدی- خییر')
    
    def get_total_allocation_cash(self):
        """Get total cash allocation from all sources."""
        return (
            self.get_total_cash_national() +
            self.get_total_cash_provincial() +
            self.get_total_cash_travel() +
            self.get_total_cash_charity()
        )
    
    def get_total_allocation_treasury(self):
        """Get total treasury allocation from all sources."""
        return (
            self.get_total_treasury_national() +
            self.get_total_treasury_provincial() +
            self.get_total_treasury_travel()
        )
    
    def get_total_subprojects_allocation(self):
        """Get total allocation across all subprojects."""
        from django.db.models import Sum
        from creator_subproject.models import SituationReport
        
        result = SituationReport.objects.filter(
            sub_project__project=self
        ).aggregate(Sum('amount'))['amount__sum']
        
        return result if result else 0

    def calculate_physical_progress(self):
        """
        Calculate the project's physical progress as a weighted mean of subprojects' physical progress.
        Weights are based on each subproject's final contract amount or imagenary_cost if no contract.
        """
        subprojects = self.subprojects.all()
        
        if not subprojects.exists():
            return 0
            
        total_weight = 0
        weighted_progress = 0
        
        for subproject in subprojects:
            # Get weight - use final_contract_amount which automatically uses imagenary_cost if no contract
            weight = subproject.final_contract_amount
            if weight is not None:
                weight = float(weight)
                # Handle None or zero progress
                progress = float(subproject.physical_progress or 0)
                
                total_weight += weight
                weighted_progress += weight * progress
        
        if total_weight > 0:
            # Calculate to more decimal places for precision, then round to 2 decimals for display
            return round(weighted_progress / total_weight, 2)
        else:
            return 0
    
    def calculate_financial_progress(self):
        """
        Calculate the financial progress percentage for the project.
        This is based on the sum of all payments divided by the total contract amount.
        """
        # Initialize variables
        total_contract_amount = 0
        total_paid_amount = 0
        
        # Get all subprojects with contracts
        subprojects = self.subprojects.filter(contract_amount__gt=0)
        
        # If no subprojects with contracts, return 0
        if not subprojects.exists():
            return 0
        
        # Calculate totals
        for subproject in subprojects:
            # Only include subprojects with contracts
            if subproject.contract_amount and subproject.contract_amount > 0:
                # Add to total contract amount
                total_contract_amount += subproject.final_contract_amount
                
                # Use financial_progress_amount property instead of directly accessing database fields
                progress_amount = 0
                try:
                    # Call the property which is calculated on the fly
                    progress_amount = float(subproject.financial_progress_amount)
                except (AttributeError, ValueError):
                    # If property doesn't exist or can't be converted, use 0
                    progress_amount = 0
                
                total_paid_amount += progress_amount
        
        # Calculate percentage
        if total_contract_amount > 0:
            percentage = (total_paid_amount / float(total_contract_amount)) * 100
            return min(round(percentage, 2), 100)
        else:
            return 0

    def calculate_total_debt(self):
        """
        Calculate the total debt for the project.
        This is the sum of all subprojects' debts (دیون زیرپروژه ها).
        """
        from django.db.models import Sum
        
        # Sum all subproject debts using the subproject_debt field
        result = self.subprojects.aggregate(
            total_debt=Sum('subproject_debt')
        )['total_debt']
        
        return result if result is not None else 0
    
    def get_total_required_credit_for_contract_completion(self):
        """
        Calculate the total required credit for contract completion of all subprojects.
        This is the sum of all subprojects' required credit for contract completion.
        Only includes subprojects that have contract information.
        اعتبار مورد نیاز تکمیل قرار داد های زیر پروژه ها
        """
        total_required_credit = 0
        
        for subproject in self.subprojects.all():
            # Check if subproject has contract information
            has_contract_info = (
                hasattr(subproject, 'contract_amount') and 
                subproject.contract_amount is not None and 
                subproject.contract_amount > 0 and
                subproject.contract_start_date is not None and
                subproject.contract_end_date is not None and
                subproject.contract_type is not None and
                subproject.contract_type != 'فاقد قرارداد'
            )
            
            # Only include subprojects with contract information
            if has_contract_info:
                try:
                    required_credit = float(subproject.required_credit_for_contract_completion)
                    total_required_credit += required_credit
                except (AttributeError, ValueError, TypeError):
                    # If property doesn't exist or can't be converted, skip this subproject
                    pass
        
        return total_required_credit
    
    def get_total_required_credit_for_project_completion(self):
        """
        Calculate the total required credit for project completion.
        This includes:
        - Sum of "اعتبار مورد نیاز تکمیل قرار داد" for subprojects with contract information
        - Plus sum of "هزینه تخمینی" for subprojects without contract information
        اعتبار مورد نیاز تکمیل پروژه
        """
        total_required_credit = 0
        
        for subproject in self.subprojects.all():
            # Check if subproject has contract information
            has_contract_info = (
                hasattr(subproject, 'contract_amount') and 
                subproject.contract_amount is not None and 
                subproject.contract_amount > 0 and
                subproject.contract_start_date is not None and
                subproject.contract_end_date is not None and
                subproject.contract_type is not None and
                subproject.contract_type != 'فاقد قرارداد' and
                subproject.execution_method is not None
            )
            
            if has_contract_info:
                # For subprojects with contract, use required credit for contract completion
                try:
                    required_credit = float(subproject.required_credit_for_contract_completion)
                    total_required_credit += required_credit
                except (AttributeError, ValueError, TypeError):
                    # If property doesn't exist or can't be converted, skip this subproject
                    pass
            else:
                # For subprojects without contract, use estimated cost (imagenrary_cost)
                try:
                    if hasattr(subproject, 'imagenrary_cost') and subproject.imagenrary_cost:
                        estimated_cost = float(subproject.imagenrary_cost)
                        total_required_credit += estimated_cost
                except (AttributeError, ValueError, TypeError):
                    # If field doesn't exist or can't be converted, skip this subproject
                    pass
        
        return total_required_credit
    
    def get_total_latest_payments(self):
        """
        Calculate the total payment amount from the latest situation reports of all subprojects.
        
        Returns:
            The sum of payment amounts from the latest situation reports
        """
        subprojects = self.subprojects.all()
        
        if not subprojects.exists():
            return 0
            
        total_payment_amount = 0
        
        for subproject in subprojects:
            # Get the latest situation report for this subproject
            latest_report = subproject.latest_situation_report
            if latest_report:
                total_payment_amount += float(latest_report.payment_amount)
        
        return total_payment_amount
    
    def get_total_contract_amount(self):
        """
        Calculate the total contract amount from all subprojects.
        Sum of field 'مبلغ نهایی قرارداد' (final_contract_amount) for all subprojects that have contracts.
        Only includes subprojects with complete contract information.
        
        Returns:
            The sum of final contract amounts from subprojects with complete contract information
        """
        total_amount = 0
        
        for subproject in self.subprojects.all():
            # Check if the subproject has complete contract information
            has_contract_info = (
                hasattr(subproject, 'final_contract_amount') and 
                subproject.final_contract_amount is not None and 
                subproject.final_contract_amount > 0 and
                subproject.contract_start_date is not None and
                subproject.contract_end_date is not None and
                subproject.contract_amount is not None and
                subproject.contract_amount > 0 and
                subproject.contract_type is not None and
                subproject.contract_type != 'فاقد قرارداد' and
                subproject.execution_method is not None
            )
            
            if has_contract_info:
                total_amount += float(subproject.final_contract_amount)
                
        return total_amount
    
    def calculate_overall_status(self):
        """
        Calculate the project's overall status based on subprojects' statuses:
        - "فعال" if any subproject has state "فعال"
        - "تامین اعتبار" if no "فعال" subprojects but at least one has state "تامین اعتبار"
        - "غیره فعال" otherwise
        """
        subprojects = self.subprojects.all()
        
        if not subprojects.exists():
            return "غیره فعال"
            
        has_active = False
        has_funding = False
        
        for subproject in subprojects:
            if subproject.state == "فعال":
                has_active = True
                break
            elif subproject.state == "تامین اعتبار":
                has_funding = True
        
        if has_active:
            return "فعال"
        elif has_funding:
            return "تامین اعتبار"
        else:
            return "غیره فعال"
    
    def update_cached_financial_values(self):
        """Update cached financial calculation values."""
        self.cached_total_debt = self.calculate_total_debt()
        self.cached_required_credit_contracts = self.get_total_required_credit_for_contract_completion()
        self.cached_required_credit_project = self.get_total_required_credit_for_project_completion()
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        
        # If program is set, automatically set the province and city from the program
        if self.program:
            if self.program.province:
                self.province = self.program.province
            if self.program.city:
                self.city = self.program.city
            
        # Calculate physical progress based on subprojects before saving
        if not is_new:  # Only for existing projects
            self.physical_progress = self.calculate_physical_progress()
            self.overall_status = self.calculate_overall_status()
            
            # Update cached financial values - only for existing projects
            # For new projects, these will be 0 since no subprojects exist yet
            self.update_cached_financial_values()
            
        super().save(*args, **kwargs)


# Auto-generate project_id before saving
@receiver(pre_save, sender=Project)
def set_project_id(sender, instance, **kwargs):
    if not instance.project_id:
        instance.project_id = generate_unique_project_id()


class ALL_Project(models.Model):
    """Summary table for all projects."""
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='summary')
    name = models.CharField(max_length=255)
    province = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    project_type = models.CharField(max_length=50)
    physical_progress = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total_allocation_cash = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    total_allocation_treasury = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    created_by = models.CharField(max_length=100)  # Username of the creator
    created_at = models.DateTimeField()
    is_approved = models.BooleanField(default=False)
    subproject_count = models.PositiveSmallIntegerField(default=0)
    
    class Meta:
        verbose_name = "خلاصه پروژه"
        verbose_name_plural = "خلاصه پروژه‌ها"
    
    def __str__(self):
        return f"Summary: {self.name} ({self.project.project_id})"
    
    @classmethod
    def create_project(cls, name, project_type, province, city, license_state, license_code,
                      user, is_approved=False, physical_progress=0, **kwargs):
        """
        Create a new Project and its associated ALL_Project entry in one step.
        
        Args:
            name: Project name
            project_type: Type of project
            province: Province
            city: City
            license_state: License state
            license_code: License code
            user: User creating the project
            is_approved: Whether the project is approved (default: False)
            physical_progress: Initial physical progress (default: 0)
            **kwargs: Additional fields for the Project model
            
        Returns:
            A tuple of (Project instance, ALL_Project instance)
        """
        # Create the project first
        project = Project.objects.create(
            name=name,
            project_type=project_type,
            province=province,
            city=city,
            physical_progress=physical_progress,
            created_by=user,
            is_approved=is_approved,
            **kwargs
        )
        
        # The ALL_Project entry is automatically created by the post_save signal
        # We just need to retrieve it
        return project, project.summary
    
    def create_subproject(self, sub_project_type, start_date, state, remaining_work, 
                         estimated_opening_time, contract_start_date, contract_end_date, contract_amount,
                         contract_type, execution_method, is_suportting_charity='ندارد', user=None):
        """
        Create a new subproject through the ALL_Project entry.
        This is a convenience method that delegates to the Project.create_subproject method.
        
        Args:
            Same as Project.create_subproject
            
        Returns:
            The created SubProject instance, or None if max subproject limit reached
        """
        return self.project.create_subproject(
            sub_project_type=sub_project_type,
            start_date=start_date,
            state=state,
            remaining_work=remaining_work,
            estimated_opening_time=estimated_opening_time,
            contract_start_date=contract_start_date,
            contract_end_date=contract_end_date,
            contract_amount=contract_amount,
            contract_type=contract_type,
            execution_method=execution_method,
            is_suportting_charity=is_suportting_charity,
            user=user
        )
    
    def get_subprojects(self):
        """Returns all subprojects for this project summary."""
        return self.project.get_all_subprojects()
    
    def get_subproject_count(self):
        """Returns the current number of subprojects."""
        return self.project.get_subproject_count()
    
    def get_total_allocation(self):
        """Returns the total allocation for this project."""
        return float(self.total_allocation_cash) + float(self.total_allocation_treasury)


# Create or update ALL_Project entry when a Project is saved
@receiver(post_save, sender=Project)
def update_all_project(sender, instance, created, **kwargs):
    # Calculate total allocations
    total_allocation_cash = instance.get_total_allocation_cash()
    total_allocation_treasury = instance.get_total_allocation_treasury()
    
    # Get subproject count - but only if this is not a newly created project
    # For newly created projects, subproject count is 0 since no subprojects exist yet
    if created:
        subproject_count = 0
    else:
        subproject_count = instance.get_subproject_count()
    
    # Create or update the ALL_Project entry
    ALL_Project.objects.update_or_create(
        project=instance,
        defaults={
            'name': instance.name,
            'province': instance.province,
            'city': instance.city,
            'project_type': instance.project_type,
            'physical_progress': instance.physical_progress,
            'total_allocation_cash': total_allocation_cash,
            'total_allocation_treasury': total_allocation_treasury,
            'created_by': instance.created_by.username,
            'created_at': instance.created_at,
            'is_approved': instance.is_approved,
            'subproject_count': subproject_count
        }
    )


class AllocationCreditCash(models.Model):
    SOURCE_CHOICES = [
        ('ملی', 'ملی'),
        ('استانی', 'استانی'),
        
        ('مصوبات سفر', 'مصوبات سفر'),
        ('درآمد مرکز', 'درآمد مرکز'),
        ('خیرساز', 'خیرساز'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='cash_allocations')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES)
    date_added = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.project.name} - {self.source} - {self.amount}"


class AllocationCreditTreasury(models.Model):
    SOURCE_CHOICES = [
        ('ملی', 'ملی'),
        ('استانی', 'استانی'),
        ('مصوبات سفر', 'مصوبات سفر'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='treasury_allocations')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES)
    date_added = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.project.name} - {self.source} - {self.amount}"


class ProjectUpdateHistory(models.Model):
    """Model to track project update history."""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='update_history')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='project_updates')
    updated_at = models.DateTimeField(auto_now_add=True)
    field_name = models.CharField(max_length=50)
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "تاریخچه بروزرسانی پروژه"
        verbose_name_plural = "تاریخچه بروزرسانی پروژه‌ها"
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.project.name} - {self.field_name} - {self.updated_at}"


@receiver(pre_save, sender=Project)
def track_project_changes(sender, instance, **kwargs):
    """Record changes to project fields when project is updated."""
    # Skip for new projects
    if not instance.pk:
        return
    
    try:
        # Get current state of the project from the database
        old_instance = Project.objects.get(pk=instance.pk)
        
        # Skip for created/new projects
        if not old_instance:
            return
            
        # Track changes to fields
        tracked_fields = [
            'name', 'province', 'city', 'project_type', 
            'program', 'physical_progress', 'is_approved', 'is_submitted'
        ]
        
        updates = []
        for field in tracked_fields:
            old_value = getattr(old_instance, field)
            new_value = getattr(instance, field)
            
            # Record if value changed
            if old_value != new_value:
                # Convert non-string values to string for storage
                old_str = str(old_value)
                new_str = str(new_value)
                
                # Create ProjectUpdateHistory entry but don't save yet
                # It will be saved after the project is saved
                updates.append({
                    'field': field,
                    'old': old_str,
                    'new': new_str
                })
        
        # Store updates to be processed after save
        if updates:
            instance._pending_updates = updates
    
    except Exception:
        # If any error occurs, just continue without tracking
        pass
        

@receiver(post_save, sender=Project)
def save_project_updates(sender, instance, created, **kwargs):
    """Save the tracked changes after project is saved."""
    # Skip for new projects
    if created:
        return
        
    # Check if there are pending updates to save
    if hasattr(instance, '_pending_updates') and instance._pending_updates:
        # Get the user if available
        user = getattr(instance, '_update_user', instance.created_by)
        
        # Save all tracked changes
        for update in instance._pending_updates:
            ProjectUpdateHistory.objects.create(
                project=instance,
                updated_by=user,
                field_name=update['field'],
                old_value=update['old'],
                new_value=update['new']
            )


class ProjectRejectionComment(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='rejection_comments')
    expert = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='project_rejection_comments')
    field_name = models.CharField(max_length=100)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "نظر رد پروژه"
        verbose_name_plural = "نظرات رد پروژه"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment on {self.field_name} by {self.expert.username}"


class ProjectFinancialAllocation(models.Model):
    """Model for tracking financial allocations for projects"""
    
    TYPE_CHOICES = [
        ('اعتبار نقدی-ملی', 'اعتبار نقدی-ملی'),
        ('اعتبار نقدی-استانی', 'اعتبار نقدی-استانی'),
        ('اعتبار نقدی-سفر', 'اعتبار نقدی-سفر'),
        ('اعتبار اسناد خزانه-ملی', 'اعتبار اسناد خزانه-ملی'),
        ('اعتبار اسناد خزانه-استانی', 'اعتبار اسناد خزانه-استانی'),
        ('اعتبار اسناد خزانه-سفر', 'اعتبار اسناد خزانه-سفر'),
        ('نقدی- خییر', 'نقدی- خییر'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='allocations')
    amount = models.DecimalField(max_digits=15, decimal_places=0, verbose_name="مبلغ")
    letter_number = models.CharField(max_length=100, verbose_name="شماره نامه")
    allocation_type = models.CharField(max_length=50, choices=TYPE_CHOICES, verbose_name="نوع تخصیص")
    allocation_date = models.DateField(verbose_name="تاریخ تخصیص", default=timezone.now)
    description = models.TextField(blank=True, verbose_name="توضیحات")
    
    class Meta:
        verbose_name = "تخصیص مالی پروژه"
        verbose_name_plural = "تخصیص‌های مالی پروژه"
        ordering = ['-allocation_date']
    
    def __str__(self):
        return f"{self.project.name} - {self.allocation_type} - {self.amount} ریال"


# Add a post_save signal to Project model
@receiver(post_save, sender=Project)
def clear_rejection_comments_on_draft(sender, instance, **kwargs):
    """
    Clear rejection comments when project status changes to draft
    """
    if not instance.is_submitted:
        # If project is set to draft, delete all rejection comments
        # BUT only if there are no recent rejection comments (within last 5 minutes)
        # This prevents deleting rejection comments that were just created during rejection
        from django.utils import timezone
        from datetime import timedelta
        
        recent_cutoff = timezone.now() - timedelta(minutes=5)
        recent_rejection_comments = ProjectRejectionComment.objects.filter(
            project=instance,
            created_at__gte=recent_cutoff
        )
        
        if not recent_rejection_comments.exists():
            # Only delete if there are no recent rejection comments
            ProjectRejectionComment.objects.filter(project=instance).delete()


@receiver(post_save, sender=ProjectRejectionComment)
def send_sms_on_project_rejection_comment(sender, instance, created, **kwargs):
    """
    Send SMS notification when a project rejection comment is created
    """
    if created:  # Only send on create
        try:
            import logging
            logger = logging.getLogger(__name__)
            
            from notifications_sms.models import SMSSettings
            from notifications_sms.utils import IPPanelSMSSender, get_default_template
            from django.db import transaction
            
            logger.info(f"Project rejection comment created for project: {instance.project.name}")
            
            # Check if auto SMS for rejected projects is enabled
            sms_settings = SMSSettings.get_settings()
            if not sms_settings.auto_send_rejected:
                logger.warning("Auto send rejected is disabled in SMS settings")
                return
            
            # Get the project creator/owner
            project = instance.project
            creator = project.created_by
            
            # Skip if creator has no phone number
            if not creator or not creator.phone_number:
                logger.warning(f"Creator has no phone number for project: {project.name}")
                return
            
            logger.info(f"Sending rejection SMS to {creator.phone_number} for project: {project.name}")
            
            # Get the PROJECT_REJECTED template
            template = get_default_template('PROJECT_REJECTED')
            
            if template:
                logger.info(f"Using template: {template.name}")
                # Use the simple template content directly since it should be "پروژه رد شده"
                message = template.content
                
                # If the template has variables, replace them
                if '{' in message:
                    context_vars = {
                        'first_name': creator.first_name or creator.username,
                        'last_name': creator.last_name or '',
                        'full_name': creator.get_full_name() or creator.username,
                        'role': creator.get_role_display() if hasattr(creator, 'get_role_display') else '',
                        'rejection_reason': instance.comment,
                        'expert_name': instance.expert.get_full_name() or instance.expert.username,
                        'rejection_date': instance.created_at.strftime('%Y/%m/%d'),
                        'project_name': project.name,
                        'project_id': project.project_id or str(project.id)
                    }
                    
                    # Replace variables in template content
                    for var, value in context_vars.items():
                        message = message.replace(f'{{{var}}}', str(value))
            else:
                # Fallback message
                logger.warning("No PROJECT_REJECTED template found, using fallback message")
                message = f"با سلام وعرض ادب خدمت همکار گرامی به دلیل زیر پروژه نیازمند اصلاح است: {instance.comment}"
            
            logger.info(f"SMS message to send: {message}")
            
            # Send SMS using transaction to ensure atomicity
            with transaction.atomic():
                result = IPPanelSMSSender.send_sms(
                    recipient_number=creator.phone_number,
                    message=message,
                    sender_user=instance.expert,
                    recipient_user=creator,
                    template=template
                )
                
                logger.info(f"SMS send result: {result}")
                
                # Also create entry in old SMS log system for compatibility with "گزارش پیامک‌ها" dashboard
                from notifications.models import SMSLog as OldSMSLog
                try:
                    old_log_status = 'sent' if result.get('status') == 'OK' else 'failed'
                    old_sms_log = OldSMSLog.objects.create(
                        recipient=creator,
                        message=message,
                        project_name=project.name,
                        project_id=project.project_id or str(project.id),
                        province=project.province,
                        status=old_log_status,
                        message_id=result.get('message_id', ''),
                        error_message=result.get('message', '') if result.get('status') != 'OK' else ''
                    )
                    logger.info(f"Created old SMS log entry: {old_sms_log.id}")
                except Exception as old_log_error:
                    # Don't let old log creation fail the main process
                    logger.warning(f"Failed to create old SMS log: {old_log_error}")
                
                if result.get('status') == 'OK':
                    logger.info(f"SMS sent successfully to {creator.phone_number} for project rejection")
                else:
                    logger.error(f"Failed to send SMS: {result.get('message', 'Unknown error')}")
            
        except Exception as e:
            # Log the error but don't raise it to avoid breaking the rejection process
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error sending rejection SMS for project {instance.project.name}: {str(e)}", exc_info=True)


class FundingRequest(models.Model):
    """Model for funding requests (درخواست اعتبار)"""
    
    PRIORITY_CHOICES = [
        ('خیلی زیاد', 'خیلی زیاد'),
        ('زیاد', 'زیاد'),
        ('متوسط', 'متوسط'),
        ('کم', 'کم'),
        ('خیلی کم', 'خیلی کم'),
    ]
    
    STATUS_CHOICES = [
        ('پیش‌نویس', 'پیش‌نویس'),
        ('ارسال شده به کارشناس', 'ارسال شده به کارشناس'),
        ('رد شده توسط کارشناس', 'رد شده توسط کارشناس'),
        ('تایید شده توسط کارشناس', 'تایید شده توسط کارشناس'),
        ('ارسال شده به رئیس', 'ارسال شده به رئیس'),
        ('رد شده توسط رئیس', 'رد شده توسط رئیس'),
        ('تایید شده', 'تایید شده'),
        ('در تاریخچه', 'در تاریخچه'),
    ]
    
    # Basic information
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='funding_requests', verbose_name="پروژه")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                                  related_name='created_funding_requests', verbose_name="ایجاد کننده")
    
    # Province information (filled by province user)
    province_suggested_amount = models.DecimalField(max_digits=15, decimal_places=0, 
                                                   verbose_name="مبلغ پیشنهادی استان",
                                                   help_text="مبلغ پیشنهادی توسط استان")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, 
                               verbose_name="اولویت",
                               help_text="میزان اولویت درخواست")
    province_description = models.TextField(verbose_name="توضیحات استان", 
                                           help_text="توضیحات تکمیلی استان")
    
    # Expert information (filled by expert user)
    expert_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                   null=True, blank=True, related_name='reviewed_funding_requests',
                                   verbose_name="کارشناس بررسی کننده")
    headquarters_suggested_amount = models.DecimalField(max_digits=15, decimal_places=0, 
                                                      null=True, blank=True,
                                                      verbose_name="مبلغ پیشنهادی ستاد",
                                                      help_text="مبلغ پیشنهادی توسط کارشناس ستاد")
    expert_description = models.TextField(blank=True, verbose_name="توضیحات کارشناس",
                                         help_text="توضیحات تکمیلی کارشناس")
    expert_rejection_reason = models.TextField(blank=True, verbose_name="دلیل رد توسط کارشناس", 
                                             help_text="دلیل رد درخواست توسط کارشناس")
    
    # Chief information (filled by chief user)
    chief_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                  null=True, blank=True, related_name='approved_funding_requests',
                                  verbose_name="رئیس بررسی کننده")
    final_amount = models.DecimalField(max_digits=15, decimal_places=0, 
                                      null=True, blank=True,
                                      verbose_name="مبلغ نهایی",
                                      help_text="مبلغ نهایی مصوب")
    chief_rejection_reason = models.TextField(blank=True, verbose_name="دلیل رد توسط رئیس", 
                                            help_text="دلیل رد درخواست توسط رئیس")
    
    # Status tracking
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, 
                             default='پیش‌نویس', verbose_name="وضعیت")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")
    submitted_at = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ ارسال")
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ تایید")
    archived_at = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ آرشیو")
    
    class Meta:
        verbose_name = "درخواست اعتبار"
        verbose_name_plural = "درخواست‌های اعتبار"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"درخواست اعتبار {self.project.name} - {self.get_status_display()}"
    
    def submit_to_expert(self, expert_user=None):
        """Submit the funding request to an expert for review"""
        if not expert_user and self.project.province:
            # Try to find an expert assigned to this province
            from accounts.models import ExpertProvince, User
            expert_provinces = ExpertProvince.objects.filter(province=self.project.province)
            if expert_provinces.exists():
                expert_user = expert_provinces.first().expert
        
        if expert_user:
            self.expert_user = expert_user
            self.status = 'ارسال شده به کارشناس'
            self.submitted_at = timezone.now()
            self.save()
            return True
        return False
    
    def expert_approve(self):
        """Expert approves and sends to chief"""
        self.status = 'تایید شده توسط کارشناس'
        self.save()
        return True
    
    def expert_reject(self, reason):
        """Expert rejects with a reason"""
        if not reason:
            return False
        
        self.expert_rejection_reason = reason
        self.status = 'رد شده توسط کارشناس'
        self.save()
        return True
    
    def send_to_chief(self, chief_user=None):
        """Send approved request to chief executive"""
        if not chief_user:
            # Try to find a chief executive
            from accounts.models import User
            chiefs = User.objects.filter(role='CHIEF_EXECUTIVE')
            if chiefs.exists():
                chief_user = chiefs.first()
        
        if chief_user:
            self.chief_user = chief_user
            self.status = 'ارسال شده به رئیس'
            self.save()
            return True
        return False
    
    def chief_approve(self, final_amount=None):
        """Chief approves with final amount"""
        if final_amount is not None:
            self.final_amount = final_amount
        elif not self.final_amount:
            self.final_amount = self.headquarters_suggested_amount or self.province_suggested_amount
            
        self.status = 'تایید شده'
        self.approved_at = timezone.now()
        self.save()
        
        # Send SMS notification to project creator
        try:
            from notifications_sms.utils import IPPanelSMSSender
            from notifications_sms.models import SMSTemplate
            from django.utils import timezone as tz
            from django.db import transaction
            
            # Get the default template for funding request approval
            template = SMSTemplate.objects.filter(
                type=SMSTemplate.FUNDING_REQUEST_APPROVED,
                is_default=True
            ).first()
            
            if template and self.created_by.phone_number:
                # Prepare context variables for the template
                context_vars = {
                    'first_name': self.created_by.first_name or self.created_by.username,
                    'last_name': self.created_by.last_name,
                    'full_name': self.created_by.get_full_name() or self.created_by.username,
                    'role': self.created_by.get_role_display() if hasattr(self.created_by, 'get_role_display') else '',
                    'province': str(self.created_by.province) if hasattr(self.created_by, 'province') and self.created_by.province else '',
                    'project_name': self.project.name,
                    'final_amount': f"{self.final_amount:,.0f}" if self.final_amount else '0',
                    'province_amount': f"{self.province_suggested_amount:,.0f}" if self.province_suggested_amount else '0',
                    'approval_date': tz.localtime(self.approved_at).strftime('%Y/%m/%d') if self.approved_at else '',
                    'chief_name': self.chief_user.get_full_name() if self.chief_user else '',
                    'expert_name': self.expert_user.get_full_name() if self.expert_user else '',
                }
                
                # Replace variables in template content
                message_content = template.content
                for var, value in context_vars.items():
                    message_content = message_content.replace(f'{{{var}}}', str(value))
                
                # Send SMS using transaction to ensure atomicity
                with transaction.atomic():
                    IPPanelSMSSender.send_sms(
                        recipient_number=self.created_by.phone_number,
                        message=message_content,
                        sender_user=self.chief_user,
                        recipient_user=self.created_by,
                        template=template
                    )
                    
        except Exception as e:
            # Log the error but don't prevent the approval from completing
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send SMS notification for funding approval: {str(e)}")
        
        return True
    
    def chief_reject(self, reason):
        """Chief rejects with a reason"""
        if not reason:
            return False
            
        self.chief_rejection_reason = reason
        self.status = 'رد شده توسط رئیس'
        self.save()
        return True
    
    def archive(self):
        """Move to archive/history"""
        self.status = 'در تاریخچه'
        self.archived_at = timezone.now()
        self.save()
        return True


# Update project financial values when subproject changes
def update_project_financial_cache(sender, instance, **kwargs):
    """Update project cached financial values when subproject data changes."""
    try:
        project = instance.project if hasattr(instance, 'project') else instance
        if hasattr(project, 'update_cached_financial_values'):
            project.update_cached_financial_values()
            # Use update to avoid triggering save signals
            Project.objects.filter(pk=project.pk).update(
                cached_total_debt=project.cached_total_debt,
                cached_required_credit_contracts=project.cached_required_credit_contracts,
                cached_required_credit_project=project.cached_required_credit_project
            )
    except Exception:
        pass


# Connect signals for subproject models
try:
    from creator_subproject.models import SubProject
    post_save.connect(update_project_financial_cache, sender=SubProject)
except ImportError:
    pass

try:
    from creator_subproject.models import SituationReport
    post_save.connect(update_project_financial_cache, sender=SituationReport)
except ImportError:
    pass
