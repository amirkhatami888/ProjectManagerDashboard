from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _

# Create your models here.

class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'ADMIN')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(username, email, password, **extra_fields)

class User(AbstractUser):
    ROLE_CHOICES = (
        ('ADMIN', _('Admin')),
        ('CEO', _('CEO')),
        ('CHIEF_EXECUTIVE', _('Chief Executive')),
        ('VICE_CHIEF_EXECUTIVE', _('Vice Chief Executive')),
        ('EXPERT', _('Expert')),
        ('PROVINCE_MANAGER', _('Province Manager')),
    )
    
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
        ('اردبیل', 'اردبیل'),
    ]
    
    email = models.EmailField(_('email address'), unique=True)
    role = models.CharField(_('role'), max_length=20, choices=ROLE_CHOICES, default='PROVINCE_MANAGER')
    province = models.CharField(_('province'), max_length=50, blank=True, null=True)
    phone_number = models.CharField(_('phone number'), max_length=15, blank=True, null=True)
    profile_picture = models.ImageField(_('profile picture'), upload_to='profile_pics/', blank=True, null=True)
    نام = models.CharField(_('first name'), max_length=100, blank=True, null=True)
    نام_خانوادگی = models.CharField(_('last name'), max_length=100, blank=True, null=True)
    سمت = models.CharField(_('position'), max_length=100, blank=True, null=True)
    
    objects = CustomUserManager()
    
    def __str__(self):
        return self.username
    
    @property
    def is_admin(self):
        return self.role == 'ADMIN'
    
    @property
    def is_ceo(self):
        return self.role == 'CEO'
    
    @property
    def is_chief_executive(self):
        return self.role == 'CHIEF_EXECUTIVE'
    
    @property
    def is_vice_chief_executive(self):
        return self.role == 'VICE_CHIEF_EXECUTIVE'
    
    @property
    def is_expert(self):
        return self.role == 'EXPERT'
    
    @property
    def is_province_manager(self):
        return self.role == 'PROVINCE_MANAGER'
        
    def get_assigned_provinces(self):
        """Get all provinces assigned to this user based on their role"""
        if self.is_expert:
            return list(self.expert_provinces.values_list('province', flat=True))
        elif self.is_province_manager or self.is_vice_chief_executive:
            return list(self.user_provinces.values_list('province', flat=True))
        elif self.is_admin or self.is_ceo or self.is_chief_executive:
            # These roles have access to all provinces
            return [province[0] for province in self.PROVINCE_CHOICES]
        return []
        
    def has_province_access(self, province_name):
        """Check if user has access to the specified province"""
        if self.is_admin or self.is_ceo or self.is_chief_executive:
            return True
        
        assigned_provinces = self.get_assigned_provinces()
        return province_name in assigned_provinces

class ExpertProvince(models.Model):
    """Model for tracking which provinces an expert is assigned to"""
    expert = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expert_provinces')
    province = models.CharField(_('province'), max_length=50, choices=User.PROVINCE_CHOICES)
    
    class Meta:
        verbose_name = _("Expert Province Assignment")
        verbose_name_plural = _("Expert Province Assignments")
        unique_together = ('expert', 'province')
    
    def __str__(self):
        return f"{self.expert.username} - {self.province}"

class UserProvince(models.Model):
    """Model for tracking which provinces a user is assigned to"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_provinces')
    province = models.CharField(_('province'), max_length=50, choices=User.PROVINCE_CHOICES)
    
    class Meta:
        verbose_name = _("User Province Assignment")
        verbose_name_plural = _("User Province Assignments")
        unique_together = ('user', 'province')
    
    def __str__(self):
        return f"{self.user.username} - {self.province}"
