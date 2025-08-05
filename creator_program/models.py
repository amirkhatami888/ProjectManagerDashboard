from django.db import models
from django.conf import settings
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone
import random


def generate_unique_program_id():
    """Generate a unique 6-digit program ID not used by any existing program."""
    while True:
        program_id = str(random.randint(100000, 999999))
        if not Program.objects.filter(program_id=program_id).exists():
            return program_id


class Program(models.Model):
    """
    Program ('طرح') model - the top level in the hierarchy
    Program -> Project -> SubProject
    """
    
    # Using the same choices as Project's project_type
    PROGRAM_TYPE_CHOICES = [
        ('پایگاه امداد جادهای', 'پایگاه امداد جادهای'),
        ('پایگاه امداد کوهستانی', 'پایگاه امداد کوهستانی'),
        ('پایگاه امداد دریایی', 'پایگاه امداد دریایی'),
        ('ساختمان اداری آموزشی درمانی وفرهنگی', 'ساختمان اداری آموزشی درمانی وفرهنگی'),
        ('پایگاه عملیات پشتیبانی اقماری هوایی', 'پایگاه عملیات پشتیبانی اقماری هوایی'),
        ('مولد سازی', 'مولد سازی'),
        ('سالن چند منظوره/انبار امدادی', 'سالن چند منظوره/انبار امدادی'),
    ]
    
    # Using the same choices as Project's license_state
    LICENSE_STATE_CHOICES = [
        ("دارد", "دارد"),
        ("ندارد", "ندارد"),
        ("دردست اقدام", "دردست اقدام"),
        ("قبل از بخش نامه اردیبهشت 91", "قبل از بخش نامه اردیبهشت 91")
    ]
    
    # Define province choices directly (copied from Project model)
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
    
    # Basic information
    title = models.CharField(max_length=255, verbose_name="عنوان طرح")
    program_id = models.CharField(max_length=50, unique=True, blank=True, verbose_name="کد طرح")
    program_type = models.CharField(max_length=50, choices=PROGRAM_TYPE_CHOICES, verbose_name="نوع طرح")
    province = models.CharField(max_length=50, choices=PROVINCE_CHOICES, verbose_name="استان", default="تهران")
    city = models.CharField(max_length=50, verbose_name="شهر", blank=True, null=True)
    
    # Fields moved from Project model
    license_state = models.CharField(max_length=50, choices=LICENSE_STATE_CHOICES, verbose_name="وضعیت مجوز دفترچه توجیهی")
    license_code = models.CharField(max_length=25, verbose_name="کد مجوز دفترچه توجیهی")
    
    # Address and location fields
    address = models.TextField(blank=True, null=True, verbose_name="آدرس")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True, verbose_name="طول جغرافیایی")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True, verbose_name="عرض جغرافیایی")
    
    # Optional description
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")
    
    # Calculated field for program opening date
    program_opening_date = models.DateField(null=True, blank=True, verbose_name="تاریخ افتتاح طرح")
    
    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_programs',
        verbose_name="ایجاد کننده")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")
    is_approved = models.BooleanField(default=False, verbose_name="تایید شده")
    is_submitted = models.BooleanField(default=False, verbose_name="ارسال شده")
    is_expert_approved = models.BooleanField(default=False, verbose_name="تایید کارشناس")
    
    class Meta:
        verbose_name = "طرح"
        verbose_name_plural = "طرح‌ها"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.program_id})"
    
    def get_project_count(self):
        """Returns the current number of projects in this program."""
        return self.projects.count()
    
    def get_total_subproject_count(self):
        """Returns the total number of subprojects across all projects in this program."""
        total = 0
        for project in self.projects.all():
            total += project.get_subproject_count()
        return total
    
    def calculate_overall_physical_progress(self):
        """
        Calculate the program's overall physical progress as a weighted mean of projects' physical progress.
        Weights are based on each project's total contract amount.
        """
        projects = self.projects.all()
        
        if not projects.exists():
            return 0
            
        total_weight = 0
        weighted_progress = 0
        
        for project in projects:
            # Get weight - use total contract amount from all subprojects
            weight = project.get_total_contract_amount()
            if weight is not None and weight > 0:
                weight = float(weight)
                # Handle None or zero progress
                progress = float(project.physical_progress or 0)
                
                total_weight += weight
                weighted_progress += weight * progress
        
        if total_weight > 0:
            return round(weighted_progress / total_weight, 2)
        else:
            return 0
    
    def calculate_program_opening_date(self):
        """
        Calculate the program opening date as the maximum date of all project end dates
        (estimated_opening_time) within this program.
        """
        projects = self.projects.all()
        
        if not projects.exists():
            return None
        
        # Get all project end dates that are not None
        project_end_dates = [
            project.estimated_opening_time 
            for project in projects 
            if project.estimated_opening_time is not None
        ]
        
        if not project_end_dates:
            return None
        
        # Return the maximum date
        return max(project_end_dates)
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Calculate and update program opening date
        calculated_opening_date = self.calculate_program_opening_date()
        if self.program_opening_date != calculated_opening_date:
            self.program_opening_date = calculated_opening_date
            # Save again to update the opening date
            super().save(update_fields=['program_opening_date'])


# Auto-generate program_id before saving
@receiver(pre_save, sender=Program)
def set_program_id(sender, instance, **kwargs):
    if not instance.program_id:
        instance.program_id = generate_unique_program_id()


class ProgramUpdateHistory(models.Model):
    """Model to track program update history."""
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='update_history')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='program_updates')
    updated_at = models.DateTimeField(auto_now_add=True)
    field_name = models.CharField(max_length=50)
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "تاریخچه بروزرسانی طرح"
        verbose_name_plural = "تاریخچه بروزرسانی طرح‌ها"
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.program.title} - {self.field_name} - {self.updated_at}"


@receiver(pre_save, sender=Program)
def track_program_changes(sender, instance, **kwargs):
    """Record changes to program fields when program is updated."""
    # Skip for new programs
    if not instance.pk:
        return
    
    try:
        # Get current state of the program from the database
        old_instance = Program.objects.get(pk=instance.pk)
        
        # Skip for created/new programs
        if not old_instance:
            return
            
        # Track changes to fields
        tracked_fields = [
            'title', 'program_type', 'license_state', 'license_code',
            'description', 'is_approved', 'is_submitted'
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
                
                # Create ProgramUpdateHistory entry but don't save yet
                # It will be saved after the program is saved
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


@receiver(post_save, sender=Program)
def save_program_updates(sender, instance, created, **kwargs):
    """Save the tracked changes after program is saved."""
    # Skip for new programs
    if created:
        return
        
    # Check if there are pending updates to save
    if hasattr(instance, '_pending_updates') and instance._pending_updates:
        # Get the user if available
        user = getattr(instance, '_update_user', instance.created_by)
        
        # Save all tracked changes
        for update in instance._pending_updates:
            ProgramUpdateHistory.objects.create(
                program=instance,
                updated_by=user,
                field_name=update['field'],
                old_value=update['old'],
                new_value=update['new']
            )


class ProgramRejectionComment(models.Model):
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='rejection_comments')
    expert = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='program_rejection_comments')
    field_name = models.CharField(max_length=100)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "نظر رد طرح"
        verbose_name_plural = "نظرات رد طرح"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment on {self.field_name} by {self.expert.username}"


# Clear rejection comments when program status changes to draft
@receiver(post_save, sender=Program)
def clear_rejection_comments_on_draft(sender, instance, **kwargs):
    """
    Clear rejection comments when program status changes to draft
    """
    if not instance.is_submitted:
        # If program is set to draft, delete all rejection comments
        ProgramRejectionComment.objects.filter(program=instance).delete()


# Update program opening date when project end dates change
@receiver(post_save, sender='creator_project.Project')
def update_program_opening_date_on_project_save(sender, instance, **kwargs):
    """
    Update the program's opening date when a project's estimated_opening_time is updated.
    """
    if instance.program:
        # Recalculate the program opening date
        calculated_opening_date = instance.program.calculate_program_opening_date()
        if instance.program.program_opening_date != calculated_opening_date:
            instance.program.program_opening_date = calculated_opening_date
            instance.program.save(update_fields=['program_opening_date'])