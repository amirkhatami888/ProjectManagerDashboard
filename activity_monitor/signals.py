from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from .models import ActivityLog, ProjectChangeLog, UserSession
from .utils import log_activity, log_project_change, end_user_session, get_persian_field_label


@receiver(user_logged_in)
def user_login_handler(sender, request, user, **kwargs):
    """Handle user login events"""
    try:
        # Log the login activity
        log_activity(
            activity_type='LOGIN',
            description=f'User {user.username} logged in successfully',
            user=user,
            request=request,
            details={
                'login_method': 'form',
                'session_key': request.session.session_key if request.session else None,
            }
        )
    except Exception as e:
        print(f"Error logging user login: {e}")


@receiver(user_logged_out)
def user_logout_handler(sender, request, user, **kwargs):
    """Handle user logout events"""
    try:
        # End the user session
        if request.session and request.session.session_key:
            end_user_session(request.session.session_key)
        
        # Log the logout activity
        log_activity(
            activity_type='LOGOUT',
            description=f'User {user.username} logged out',
            user=user,
            request=request,
            details={
                'logout_method': 'form',
                'session_key': request.session.session_key if request.session else None,
            }
        )
    except Exception as e:
        print(f"Error logging user logout: {e}")


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def user_change_handler(sender, instance, created, **kwargs):
    """Handle user model changes"""
    try:
        if created:
            # New user created
            log_activity(
                activity_type='CREATE',
                description=f'New user account created: {instance.username}',
                user=instance,
                content_object=instance,
                details={
                    'email': instance.email,
                    'is_active': instance.is_active,
                    'is_staff': instance.is_staff,
                }
            )
        else:
            # User updated
            log_activity(
                activity_type='UPDATE',
                description=f'User account updated: {instance.username}',
                user=instance,
                content_object=instance,
                details={
                    'email': instance.email,
                    'is_active': instance.is_active,
                    'is_staff': instance.is_staff,
                }
            )
    except Exception as e:
        print(f"Error logging user change: {e}")


@receiver(post_delete, sender=settings.AUTH_USER_MODEL)
def user_delete_handler(sender, instance, **kwargs):
    """Handle user deletion"""
    try:
        log_activity(
            activity_type='DELETE',
            description=f'User account deleted: {instance.username}',
            user=None,  # User is being deleted
            content_object=instance,
            details={
                'email': instance.email,
                'is_active': instance.is_active,
                'is_staff': instance.is_staff,
            }
        )
    except Exception as e:
        print(f"Error logging user deletion: {e}")


# Project-related signals
@receiver(pre_save, sender='creator_project.Project')
def project_pre_save_handler(sender, instance, **kwargs):
    """Store old values before saving project"""
    if instance.pk:  # Only for existing instances
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            instance._old_values = {}
            tracked_fields = [
                'name', 'province', 'city', 'project_type', 
                'program', 'physical_progress', 'is_approved', 'is_submitted',
                'is_expert_approved', 'overall_status', 'estimated_opening_time',
                'area_size', 'site_area', 'wall_length', 'notables', 'floor'
            ]
            for field in tracked_fields:
                instance._old_values[field] = getattr(old_instance, field, None)
        except sender.DoesNotExist:
            pass

@receiver(post_save, sender='creator_project.Project')
def project_change_handler(sender, instance, created, **kwargs):
    """Handle project model changes with detailed field tracking"""
    try:
        if created:
            # New project created
            log_project_change(
                project_id=instance.project_id,
                project_name=instance.name,
                change_type='CREATE',
                change_description=f'پروژه جدید ایجاد شد: {instance.name}',
                user=instance.created_by if hasattr(instance, 'created_by') else None,
                field_name='',
                old_value='',
                new_value=instance.name,
                related_object_type='Project',
                related_object_id=instance.project_id
            )
        else:
            # Project updated - track specific field changes
            if hasattr(instance, '_old_values'):
                tracked_fields = [
                    'name', 'province', 'city', 'project_type', 
                    'program', 'physical_progress', 'is_approved', 'is_submitted',
                    'is_expert_approved', 'overall_status', 'estimated_opening_time',
                    'area_size', 'site_area', 'wall_length', 'notables', 'floor'
                ]
                
                for field in tracked_fields:
                    old_value = instance._old_values.get(field)
                    new_value = getattr(instance, field, None)
                    
                    # Skip if values are the same
                    if old_value == new_value:
                        continue
                    
                    # Handle special cases
                    if field == 'program':
                        old_value = str(old_value) if old_value else ''
                        new_value = str(new_value) if new_value else ''
                    elif field == 'estimated_opening_time':
                        old_value = old_value.strftime('%Y-%m-%d') if old_value else ''
                        new_value = new_value.strftime('%Y-%m-%d') if new_value else ''
                    
                    # Log the field change
                    log_project_change(
                        project_id=instance.project_id,
                        project_name=instance.name,
                        change_type='UPDATE',
                        change_description=f'فیلد {get_persian_field_label(field, "project")} در پروژه {instance.name} تغییر یافت',
                        user=instance.created_by if hasattr(instance, 'created_by') else None,
                        field_name=field,
                        old_value=str(old_value) if old_value is not None else '',
                        new_value=str(new_value) if new_value is not None else '',
                        related_object_type='Project',
                        related_object_id=instance.project_id
                    )
                
    except Exception as e:
        print(f"Error logging project change: {e}")


@receiver(post_delete, sender='creator_project.Project')
def project_delete_handler(sender, instance, **kwargs):
    """Handle project deletion"""
    try:
        log_project_change(
            project_id=instance.project_id,
            project_name=instance.name,
            change_type='DELETE',
            change_description=f'Project deleted: {instance.name}',
            user=None,
            field_name='',
            old_value=instance.name,
            new_value='',
            related_object_type='Project',
            related_object_id=instance.project_id
        )
    except Exception as e:
        print(f"Error logging project deletion: {e}")


# SubProject-related signals
@receiver(pre_save, sender='creator_subproject.SubProject')
def subproject_pre_save_handler(sender, instance, **kwargs):
    """Store old values before saving subproject"""
    if instance.pk:  # Only for existing instances
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            instance._old_values = {}
            tracked_fields = [
                'project_stage', 'state', 'physical_progress',
                'remaining_work', 'description', 'contract_amount',
                'contract_type', 'execution_method', 'contractor_name',
                'contractor_id', 'has_adjustment', 'adjustment_coefficient',
                'imagenary_duration', 'imagenrary_cost', 'start_date', 'end_date',
                'contract_start_date', 'contract_end_date', 'relationship_delay',
                'relationship_type', 'transaction_threshold', 'tender_type',
                'has_consultant', 'consultant_name', 'consultant_national_id'
            ]
            for field in tracked_fields:
                instance._old_values[field] = getattr(old_instance, field, None)
        except sender.DoesNotExist:
            pass

@receiver(post_save, sender='creator_subproject.SubProject')
def subproject_change_handler(sender, instance, created, **kwargs):
    """Handle subproject model changes with detailed field tracking"""
    try:
        if created:
            # New subproject created
            log_project_change(
                project_id=instance.project.project_id if instance.project else '',
                project_name=instance.project.name if instance.project else '',
                change_type='CREATE',
                change_description=f'زیرپروژه جدید ایجاد شد: {instance.name or instance.project_stage}',
                user=instance.created_by if hasattr(instance, 'created_by') else None,
                field_name='',
                old_value='',
                new_value=instance.name or instance.project_stage,
                related_object_type='SubProject',
                related_object_id=str(instance.id)
            )
        else:
            # Subproject updated - track specific field changes
            if hasattr(instance, '_old_values'):
                tracked_fields = [
                    'project_stage', 'state', 'physical_progress',
                    'remaining_work', 'description', 'contract_amount',
                    'contract_type', 'execution_method', 'contractor_name',
                    'contractor_id', 'has_adjustment', 'adjustment_coefficient',
                    'imagenary_duration', 'imagenrary_cost', 'start_date', 'end_date',
                    'contract_start_date', 'contract_end_date', 'relationship_delay',
                    'relationship_type', 'transaction_threshold', 'tender_type',
                    'has_consultant', 'consultant_name', 'consultant_national_id'
                ]
                
                for field in tracked_fields:
                    old_value = instance._old_values.get(field)
                    new_value = getattr(instance, field, None)
                    
                    # Skip if values are the same
                    if old_value == new_value:
                        continue
                    
                    # Handle date fields
                    if field in ['start_date', 'end_date', 'contract_start_date', 'contract_end_date']:
                        old_value = old_value.strftime('%Y-%m-%d') if old_value else ''
                        new_value = new_value.strftime('%Y-%m-%d') if new_value else ''
                    
                    # Log the field change
                    log_project_change(
                        project_id=instance.project.project_id if instance.project else '',
                        project_name=instance.project.name if instance.project else '',
                        change_type='UPDATE',
                        change_description=f'فیلد {get_persian_field_label(field, "subproject")} در زیرپروژه {instance.name or instance.project_stage} تغییر یافت',
                        user=instance.created_by if hasattr(instance, 'created_by') else None,
                        field_name=field,
                        old_value=str(old_value) if old_value is not None else '',
                        new_value=str(new_value) if new_value is not None else '',
                        related_object_type='SubProject',
                        related_object_id=str(instance.id)
                    )
                
    except Exception as e:
        print(f"Error logging subproject change: {e}")


@receiver(post_delete, sender='creator_subproject.SubProject')
def subproject_delete_handler(sender, instance, **kwargs):
    """Handle subproject deletion"""
    try:
        log_project_change(
            project_id=instance.project.project_id if instance.project else '',
            project_name=instance.project.name if instance.project else '',
            change_type='DELETE',
            change_description=f'Subproject deleted: {instance.name}',
            user=None,
            field_name='',
            old_value=instance.name,
            new_value='',
            related_object_type='SubProject',
            related_object_id=str(instance.id)
        )
    except Exception as e:
        print(f"Error logging subproject deletion: {e}")


# Program-related signals
@receiver(pre_save, sender='creator_program.Program')
def program_pre_save_handler(sender, instance, **kwargs):
    """Store old values before saving program"""
    if instance.pk:  # Only for existing instances
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            instance._old_values = {}
            tracked_fields = [
                'title', 'program_id', 'program_type', 'province', 'city',
                'license_state', 'license_code', 'address', 'longitude',
                'latitude', 'description', 'program_opening_date',
                'is_approved', 'is_submitted', 'is_expert_approved'
            ]
            for field in tracked_fields:
                instance._old_values[field] = getattr(old_instance, field, None)
        except sender.DoesNotExist:
            pass

@receiver(post_save, sender='creator_program.Program')
def program_change_handler(sender, instance, created, **kwargs):
    """Handle program model changes with detailed field tracking"""
    try:
        if created:
            # New program created
            log_project_change(
                project_id='',  # Programs don't have project_id
                project_name=instance.title,
                change_type='CREATE',
                change_description=f'طرح جدید ایجاد شد: {instance.title}',
                user=instance.created_by if hasattr(instance, 'created_by') else None,
                field_name='',
                old_value='',
                new_value=instance.title,
                related_object_type='Program',
                related_object_id=instance.program_id
            )
        else:
            # Program updated - track specific field changes
            if hasattr(instance, '_old_values'):
                tracked_fields = [
                    'title', 'program_id', 'program_type', 'province', 'city',
                    'license_state', 'license_code', 'address', 'longitude',
                    'latitude', 'description', 'program_opening_date',
                    'is_approved', 'is_submitted', 'is_expert_approved'
                ]
                
                for field in tracked_fields:
                    old_value = instance._old_values.get(field)
                    new_value = getattr(instance, field, None)
                    
                    # Skip if values are the same
                    if old_value == new_value:
                        continue
                    
                    # Handle date fields
                    if field == 'program_opening_date':
                        old_value = old_value.strftime('%Y-%m-%d') if old_value else ''
                        new_value = new_value.strftime('%Y-%m-%d') if new_value else ''
                    
                    # Log the field change
                    log_project_change(
                        project_id='',
                        project_name=instance.title,
                        change_type='UPDATE',
                        change_description=f'فیلد {get_persian_field_label(field, "program")} در طرح {instance.title} تغییر یافت',
                        user=instance.created_by if hasattr(instance, 'created_by') else None,
                        field_name=field,
                        old_value=str(old_value) if old_value is not None else '',
                        new_value=str(new_value) if new_value is not None else '',
                        related_object_type='Program',
                        related_object_id=instance.program_id
                    )
                
    except Exception as e:
        print(f"Error logging program change: {e}")


@receiver(post_delete, sender='creator_program.Program')
def program_delete_handler(sender, instance, **kwargs):
    """Handle program deletion"""
    try:
        log_activity(
            activity_type='DELETE',
            description=f'Program deleted: {instance.name}',
            user=None,
            content_object=instance,
            details={
                'program_name': instance.name,
                'program_type': instance.program_type if hasattr(instance, 'program_type') else '',
            }
        )
    except Exception as e:
        print(f"Error logging program deletion: {e}")


# Funding request signals
@receiver(pre_save, sender='creator_project.FundingRequest')
def funding_request_pre_save_handler(sender, instance, **kwargs):
    """Store old values before saving funding request"""
    if instance.pk:  # Only for existing instances
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            instance._old_values = {}
            tracked_fields = [
                'province_suggested_amount', 'priority', 'province_description',
                'status', 'requested_amount'
            ]
            for field in tracked_fields:
                instance._old_values[field] = getattr(old_instance, field, None)
        except sender.DoesNotExist:
            pass

@receiver(post_save, sender='creator_project.FundingRequest')
def funding_request_change_handler(sender, instance, created, **kwargs):
    """Handle funding request changes with detailed field tracking"""
    try:
        if created:
            # New funding request created
            log_project_change(
                project_id=instance.project.project_id if instance.project else '',
                project_name=instance.project.name if instance.project else '',
                change_type='FUNDING',
                change_description=f'درخواست اعتبار جدید برای پروژه {instance.project.name if instance.project else "نامشخص"} ایجاد شد',
                user=instance.created_by if hasattr(instance, 'created_by') else None,
                field_name='',
                old_value='',
                new_value=f'مبلغ: {instance.province_suggested_amount:,.0f} ریال' if hasattr(instance, 'province_suggested_amount') else '',
                related_object_type='FundingRequest',
                related_object_id=str(instance.id)
            )
        else:
            # Funding request updated - track specific field changes
            if hasattr(instance, '_old_values'):
                tracked_fields = [
                    'province_suggested_amount', 'priority', 'province_description',
                    'status', 'requested_amount'
                ]
                
                for field in tracked_fields:
                    old_value = instance._old_values.get(field)
                    new_value = getattr(instance, field, None)
                    
                    # Skip if values are the same
                    if old_value == new_value:
                        continue
                    
                    # Log the field change
                    log_project_change(
                        project_id=instance.project.project_id if instance.project else '',
                        project_name=instance.project.name if instance.project else '',
                        change_type='FUNDING',
                        change_description=f'فیلد {get_persian_field_label(field, "funding_request")} در درخواست اعتبار پروژه {instance.project.name if instance.project else "نامشخص"} تغییر یافت',
                        user=instance.created_by if hasattr(instance, 'created_by') else None,
                        field_name=field,
                        old_value=str(old_value) if old_value is not None else '',
                        new_value=str(new_value) if new_value is not None else '',
                        related_object_type='FundingRequest',
                        related_object_id=str(instance.id)
                    )
                
    except Exception as e:
        print(f"Error logging funding request change: {e}")


# Generic model change tracking
def track_model_changes(model_class, activity_type='UPDATE'):
    """Generic function to track model changes"""
    @receiver(post_save, sender=model_class)
    def model_change_handler(sender, instance, created, **kwargs):
        try:
            if created:
                log_activity(
                    activity_type='CREATE',
                    description=f'New {model_class._meta.verbose_name} created',
                    user=getattr(instance, 'created_by', None),
                    content_object=instance,
                    details={
                        'model': model_class._meta.model_name,
                        'object_id': instance.pk,
                    }
                )
            else:
                log_activity(
                    activity_type=activity_type,
                    description=f'{model_class._meta.verbose_name} updated',
                    user=getattr(instance, 'created_by', None),
                    content_object=instance,
                    details={
                        'model': model_class._meta.model_name,
                        'object_id': instance.pk,
                    }
                )
        except Exception as e:
            print(f"Error logging {model_class._meta.model_name} change: {e}")
    
    return model_change_handler


def track_model_deletion(model_class):
    """Generic function to track model deletions"""
    @receiver(post_delete, sender=model_class)
    def model_delete_handler(sender, instance, **kwargs):
        try:
            log_activity(
                activity_type='DELETE',
                description=f'{model_class._meta.verbose_name} deleted',
                user=None,
                content_object=instance,
                details={
                    'model': model_class._meta.model_name,
                    'object_id': instance.pk,
                }
            )
        except Exception as e:
            print(f"Error logging {model_class._meta.model_name} deletion: {e}")
    
    return model_delete_handler
