from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse, HttpResponseNotFound, HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, F, Sum, Case, When, Value, DecimalField, ExpressionWrapper, Max
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.urls import reverse
import json
import datetime
from dateutil.relativedelta import relativedelta
import jdatetime  # Import jdatetime for Persian date conversion
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.utils.translation import gettext as _
from django.core.exceptions import PermissionDenied
import os
from decimal import Decimal, InvalidOperation
import base64 # Added for base64 image encoding

from creator_project.models import Project, ALL_Project
from accounts.models import User
from .models import (
    SubProject, SituationReport, SubProjectRejectionComment, 
    ProjectSituation, SubProjectUpdateHistory, AdjustmentSituationReport, SubProjectGalleryImage,
    FinancialDocument, Payment, DocumentFile, FINANCIAL_DOCUMENT_TYPES
)
from .forms import (
    SubProjectForm, SubProjectRejectionForm, SituationReportForm, 
    ProjectSituationForm, AdjustmentSituationReportForm, SubProjectGalleryImageForm,
    FinancialDocumentForm, PaymentForm, DocumentFileForm
)
from .utils import jalali_to_gregorian, gregorian_to_jalali

def can_modify_project(user, project):
    """
    Check if the user has permission to modify a project.
    
    Args:
        user: The user to check permissions for
        project: The project to check
        
    Returns:
        bool: True if the user can modify the project, False otherwise
    """
    # Admin users can modify any project
    if user.is_admin:
        return True
    
    # Project creators can modify their own projects
    if project.created_by == user:
        return True
    
    # CEO and chief executives can modify any project
    if hasattr(user, 'is_ceo') and user.is_ceo:
        return True
    
    if hasattr(user, 'is_chief_executive') and user.is_chief_executive:
        return True
    
    # Province managers can modify projects from their assigned provinces
    if user.is_province_manager:
        user_provinces = user.get_assigned_provinces()
        if user_provinces and project.province in user_provinces:
            return True
    
    # Default to no access
    return False

@login_required
def subproject_list(request, project_id=None):
    # Filter by project if project_id is provided
    if project_id:
        project = get_object_or_404(Project, id=project_id)
        base_queryset = SubProject.objects.filter(project=project)
    else:
        base_queryset = SubProject.objects.all()
    
    # If user is admin, CEO, or chief executive, show all subprojects (filtered by project_id if provided)
    if request.user.is_admin or request.user.is_ceo or request.user.is_chief_executive:
        subprojects = base_queryset
    # If user is expert or vice chief executive, show submitted subprojects
    elif request.user.is_expert or request.user.is_vice_chief_executive:
        # Since we removed is_submitted, filter by parent project's status
        subprojects = base_queryset.filter(project__is_submitted=True)
    # If user is province manager, show subprojects from their assigned provinces
    elif request.user.is_province_manager:
        # Get user's assigned provinces
        user_provinces = request.user.get_assigned_provinces()
        if user_provinces:
            # Show all subprojects from projects in user's assigned provinces
            subprojects = base_queryset.filter(project__province__in=user_provinces)
        else:
            # Fallback to user's own subprojects if no province assignments
            subprojects = base_queryset.filter(created_by=request.user)
    else:
        return HttpResponseForbidden("You don't have permission to view subprojects.")

    context = {
        'subprojects': subprojects,
        'project_id': project_id
    }
    
    return render(request, 'creator_subproject/subproject_list.html', context)

@login_required
def subproject_detail(request, pk):
    """View for displaying a subproject's details."""
    subproject = get_object_or_404(SubProject, pk=pk)
    
    # Check permissions
    if not (request.user.is_admin or request.user.is_ceo or request.user.is_chief_executive or 
            request.user.is_expert or request.user == subproject.created_by or 
            request.user == subproject.project.created_by or
            (request.user.is_province_manager and subproject.project.province in request.user.get_assigned_provinces())):
        raise PermissionDenied
    
    # Get the latest financial documents
    financial_documents = subproject.financial_documents.all().order_by('-created_at')[:5]
    
    # Get the latest payments
    payments = subproject.payments.all().order_by('-created_at')[:5]
    
    # Get rejection comments if any
    rejection_comments = subproject.rejection_comments.all()
    
    # Prepare context
    context = {
        'subproject': subproject,
        'allocations': financial_documents,  # For backward compatibility in templates
        'adjustment_allocations': payments,  # For backward compatibility in templates
        'rejection_comments': rejection_comments,
        'latest_situation_report': financial_documents.first() if financial_documents else None,
        'latest_adjustment_report': payments.first() if payments else None,
    }
    
    return render(request, 'creator_subproject/subproject_detail.html', context)

def parse_jalali_date(jalali_date_str):
    """
    Parse a Jalali date string in the format YYYY/MM/DD and convert to Gregorian date
    """
    if not jalali_date_str or not jalali_date_str.strip():
        return None
        
    try:
        # Convert Persian digits to English digits if necessary
        persian_digits = '۰۱۲۳۴۵۶۷۸۹'
        english_digits = '0123456789'
        translation_table = str.maketrans(persian_digits, english_digits)
        jalali_date_en = jalali_date_str.translate(translation_table)
        
        # Clean up the string - remove any non-digit and non-slash characters
        jalali_date_clean = ''.join(c for c in jalali_date_en if c.isdigit() or c == '/')
        
        # Parse date parts
        parts = jalali_date_clean.split('/')
        if len(parts) == 3:
            year = int(parts[0])
            month = int(parts[1])
            day = int(parts[2])
            
            # Validate Persian calendar ranges
            if year < 1300 or year > 1500:
                print(f"Invalid year in date '{jalali_date_str}': {year}")
                return None
                
            if month < 1 or month > 12:
                print(f"Invalid month in date '{jalali_date_str}': {month}")
                return None
                
            if day < 1 or day > 31:
                print(f"Invalid day in date '{jalali_date_str}': {day}")
                return None
            
            # Create Jalali date and convert to Gregorian
            j_date = jdatetime.date(year, month, day)
            return j_date.togregorian()
        else:
            print(f"Invalid date format '{jalali_date_str}': expected 3 parts separated by '/', got {len(parts)} parts")
            return None
    except (ValueError, IndexError, TypeError) as e:
        print(f"Error parsing jalali date '{jalali_date_str}': {str(e)}")
    except Exception as e:
        print(f"Unexpected error parsing jalali date '{jalali_date_str}': {str(e)}")
    
    return None

def calculate_dates_based_on_relationship(subproject, post_data, related_subproject=None):
    """
    Calculate start and end dates based on relationship type and related subproject
    """
    has_contract = post_data.get('has_contract') == 'true'
    
    # With contract information, use contract dates
    if has_contract:
        contract_start_date = parse_jalali_date(post_data.get('contract_start_date'))
        contract_end_date = parse_jalali_date(post_data.get('contract_end_date'))
        
        if contract_start_date and contract_end_date:
            subproject.contract_start_date = contract_start_date
            subproject.contract_end_date = contract_end_date
            subproject.start_date = contract_start_date
            subproject.end_date = contract_end_date
        return
    
    # Without contract information
    relationship_type = post_data.get('relationship_type', '')
    delay_days = int(post_data.get('relationship_delay', 0) or 0)
    imagenary_duration = int(post_data.get('imagenary_duration', 180) or 180)
    
    # If no related subproject or missing dates, set default dates
    if not related_subproject or not hasattr(related_subproject, 'start_date') or not related_subproject.start_date or not related_subproject.end_date:
        # Set default dates if no relationship data is available
        today = timezone.now().date()
        subproject.start_date = today
        subproject.end_date = today + datetime.timedelta(days=imagenary_duration)
        return
        
    # Calculate dates based on relationship type
    if relationship_type == 'بعد از':  # After
        # Start AFTER the related project ENDS (+ delay)
        subproject.start_date = related_subproject.end_date + datetime.timedelta(days=delay_days)
        subproject.end_date = subproject.start_date + datetime.timedelta(days=imagenary_duration)
        
    elif relationship_type == 'قبل از':  # Before
        # End BEFORE the related project STARTS (- delay)
        subproject.end_date = related_subproject.start_date - datetime.timedelta(days=delay_days)
        subproject.start_date = subproject.end_date - datetime.timedelta(days=imagenary_duration)
        
    elif relationship_type == 'شروع با':  # Start With
        # Start WITH the related project START (+ delay)
        subproject.start_date = related_subproject.start_date + datetime.timedelta(days=delay_days)
        subproject.end_date = subproject.start_date + datetime.timedelta(days=imagenary_duration)
        
    elif relationship_type == 'پایان با':  # End With
        # End WITH the related project END (+ delay)
        subproject.end_date = related_subproject.end_date + datetime.timedelta(days=delay_days)
        subproject.start_date = subproject.end_date - datetime.timedelta(days=imagenary_duration)
    else:
        # Default behavior for unknown relationship type or "شناور" (floating)
        today = timezone.now().date()
        subproject.start_date = today
        subproject.end_date = today + datetime.timedelta(days=imagenary_duration)

@login_required
def subproject_create(request, project_id):
    """Create a new subproject for a project"""
    project = get_object_or_404(Project, pk=project_id)
    
    # Check if user is allowed to create subprojects for this project
    if not can_modify_project(request.user, project):
        messages.error(request, "شما مجوز دسترسی به این عملیات را ندارید.")
        return redirect('creator_project:project_list')
    
    if request.method == 'POST':
        print(f"DEBUG: POST request received for subproject creation")
        print(f"DEBUG: POST data keys: {list(request.POST.keys())}")
        print(f"DEBUG: has_contract value: {request.POST.get('has_contract')}")
        try:
            has_contract = request.POST.get('has_contract') == 'true'
            print(f"DEBUG: has_contract boolean: {has_contract}")
            
            # Step 1: Create subproject with basic data only, no relationships yet
            subproject = SubProject(
                project=project,
                name=request.POST.get('name', ''),
                sub_project_type=request.POST.get('sub_project_type'),
                sub_project_number=int(request.POST.get('sub_project_number')),
                is_suportting_charity=request.POST.get('is_suportting_charity'),
                created_by=request.user,
                state=request.POST.get('state', 'فعال')
            )
            
            # Step 2: Set non-relationship fields
            today = timezone.now().date()
            imagenary_duration = int(request.POST.get('imagenary_duration', 180) or 180)
            subproject.start_date = today
            subproject.end_date = today + datetime.timedelta(days=imagenary_duration)
            
            # Set predicted adjustment amount
            predicted_adjustment_amount = request.POST.get('predicted_adjustment_amount')
            if predicted_adjustment_amount and predicted_adjustment_amount.strip():
                try:
                    # Remove commas and any other non-numeric characters except decimal point
                    cleaned_amount = ''.join(c for c in predicted_adjustment_amount if c.isdigit() or c == '.')
                    if cleaned_amount:
                        subproject.predicted_adjustment_amount = Decimal(cleaned_amount)
                    else:
                        subproject.predicted_adjustment_amount = Decimal('0')
                except (ValueError, InvalidOperation):
                    subproject.predicted_adjustment_amount = Decimal('0')
            else:
                subproject.predicted_adjustment_amount = Decimal('0')
            
            # Save immediately to get primary key
            subproject.save()
            
            if has_contract:
                print(f"DEBUG: Processing contract fields")
                # Process contract fields
                subproject.physical_progress = Decimal(request.POST.get('physical_progress', 0))
                subproject.remaining_work = request.POST.get('remaining_work')
                
                # Parse contract dates
                print(f"DEBUG: Contract start date raw: {request.POST.get('contract_start_date')}")
                print(f"DEBUG: Contract end date raw: {request.POST.get('contract_end_date')}")
                contract_start_date = parse_jalali_date(request.POST.get('contract_start_date'))
                contract_end_date = parse_jalali_date(request.POST.get('contract_end_date'))
                print(f"DEBUG: Parsed contract start date: {contract_start_date}")
                print(f"DEBUG: Parsed contract end date: {contract_end_date}")
                
                if contract_start_date and contract_end_date:
                    subproject.contract_start_date = contract_start_date
                    subproject.contract_end_date = contract_end_date
                    subproject.start_date = contract_start_date
                    subproject.end_date = contract_end_date
                
                # Set contract fields
                contract_amount = request.POST.get('contract_amount')
                if contract_amount and contract_amount.strip():
                    try:
                        # Remove commas and any other non-numeric characters except decimal point
                        cleaned_amount = ''.join(c for c in contract_amount if c.isdigit() or c == '.')
                        if cleaned_amount:
                            subproject.contract_amount = Decimal(cleaned_amount)
                        else:
                            subproject.contract_amount = None
                    except (ValueError, InvalidOperation):
                        subproject.contract_amount = None
                else:
                    subproject.contract_amount = None
                
                # Set contract type
                subproject.contract_type = request.POST.get('contract_type')
                subproject.execution_method = request.POST.get('execution_method')
                
                # Set tender type if provided
                subproject.tender_type = request.POST.get('tender_type')
                
                # Set consultant information if applicable
                subproject.has_consultant = request.POST.get('has_consultant', 'ندارد')
                if subproject.has_consultant == 'دارد':
                    subproject.consultant_name = request.POST.get('consultant_name')
                    subproject.consultant_national_id = request.POST.get('consultant_national_id')
                
                # Set contractor information
                subproject.contractor_name = request.POST.get('contractor_name')
                subproject.contractor_id = request.POST.get('contractor_id')
                
                # Handle adjustment coefficient if applicable
                subproject.has_adjustment = request.POST.get('has_adjustment', 'ندارد')
                if subproject.has_adjustment == 'دارد':
                    adjustment_coefficient = request.POST.get('adjustment_coefficient')
                    # Remove commas before converting to Decimal
                    adjustment_coefficient = adjustment_coefficient.replace(',', '')
                    adjustment_coefficient_decimal = Decimal(adjustment_coefficient)
                    
                    # Validate adjustment coefficient is not greater than 25
                    if adjustment_coefficient_decimal > 25:
                        messages.error(request, "درصد افزایش قرارداد نمی‌تواند بیشتر از 25 درصد باشد.")
                        return redirect('creator_subproject:subproject_create', project_id=project.id)
                    
                    subproject.adjustment_coefficient = adjustment_coefficient_decimal
                else:
                    subproject.adjustment_coefficient = 0
                
                # Save the subproject with contract information
                subproject.save()
                
                # Handle relationships for contract subprojects
                related_id = request.POST.get('related_subproject')
                relationship_type = request.POST.get('relationship_type')
                
                # Only process relationship if both related_id and relationship_type are provided
                if related_id and related_id.strip() and related_id != 'floating' and relationship_type:
                    try:
                        # Convert to integer and look up the related subproject
                        related_id_int = int(related_id)
                        related_subproject = SubProject.objects.get(pk=related_id_int)
                        
                        # Update the subproject with relationship info
                        subproject.related_subproject = related_subproject
                        subproject.relationship_type = relationship_type
                        
                        # Set relationship delay if provided
                        if request.POST.get('relationship_delay'):
                            subproject.relationship_delay = int(request.POST.get('relationship_delay'))
                        
                        # Save again to update relationship fields
                        subproject.save()
                        
                        # Now calculate dates based on the relationship
                        calculate_dates_based_on_relationship(subproject, request.POST, related_subproject)
                        # Final save with updated dates
                        subproject.save()
                        
                    except ValueError:
                        messages.warning(request, "خطا: شناسه زیرپروژه مرتبط نامعتبر است.")
                    except SubProject.DoesNotExist:
                        messages.warning(request, "خطا: زیرپروژه مرتبط یافت نشد.")
                    except Exception as e:
                        messages.warning(request, f"خطا در ارتباط با زیرپروژه دیگر: {str(e)}")
                else:
                    # No relationship or floating relationship
                    calculate_dates_based_on_relationship(subproject, request.POST)
                    subproject.save()
                
                messages.success(request, "زیرپروژه با موفقیت ایجاد شد.")
                return redirect('creator_project:project_detail', pk=project.id)
                
            else:
                # For subprojects without contract
                imagenary_duration = request.POST.get('imagenary_duration')
                if imagenary_duration and imagenary_duration.strip():
                    try:
                        subproject.imagenary_duration = int(imagenary_duration)
                    except ValueError:
                        subproject.imagenary_duration = None
                else:
                    subproject.imagenary_duration = None
                
                imagenrary_cost = request.POST.get('imagenrary_cost')
                if imagenrary_cost and imagenrary_cost.strip():
                    try:
                        # Remove commas and any other non-numeric characters except decimal point
                        cleaned_cost = ''.join(c for c in imagenrary_cost if c.isdigit() or c == '.')
                        if cleaned_cost:
                            cost_decimal = Decimal(cleaned_cost)
                            # Check if the value is within valid range for DECIMAL(15,2)
                            max_value = Decimal('9999999999999.99')
                            if cost_decimal > max_value:
                                messages.error(request, f"مبلغ هزینه تخمینی خیلی بزرگ است. حداکثر مقدار مجاز: {max_value:,} ریال")
                                return redirect('creator_subproject:subproject_create', project_id=project.id)
                            subproject.imagenrary_cost = cost_decimal
                        else:
                            subproject.imagenrary_cost = None
                    except (ValueError, InvalidOperation) as e:
                        messages.error(request, f"فرمت مبلغ هزینه تخمینی نامعتبر است: {imagenrary_cost}")
                        return redirect('creator_subproject:subproject_create', project_id=project.id)
                else:
                    subproject.imagenrary_cost = None
                
                cost_calculation_method = request.POST.get('cost_calculation_method', '')
                subproject.cost_calculation_method = cost_calculation_method
                
                # Save the subproject with non-contract information
                subproject.save()
                
                # Handle relationships for non-contract subprojects
                related_id = request.POST.get('related_subproject')
                relationship_type = request.POST.get('relationship_type')
                
                # Only process relationship if both related_id and relationship_type are provided
                if related_id and related_id.strip() and related_id != 'floating' and relationship_type:
                    try:
                        # Convert to integer and look up the related subproject
                        related_id_int = int(related_id)
                        related_subproject = SubProject.objects.get(pk=related_id_int)
                        
                        # Update the subproject with relationship info
                        subproject.related_subproject = related_subproject
                        subproject.relationship_type = relationship_type
                        
                        # Set relationship delay if provided
                        if request.POST.get('relationship_delay'):
                            subproject.relationship_delay = int(request.POST.get('relationship_delay'))
                        
                        # Save again to update relationship fields
                        subproject.save()
                        
                        # Now calculate dates based on the relationship
                        calculate_dates_based_on_relationship(subproject, request.POST, related_subproject)
                        # Final save with updated dates
                        subproject.save()
                        
                    except ValueError:
                        messages.warning(request, "خطا: شناسه زیرپروژه مرتبط نامعتبر است.")
                    except SubProject.DoesNotExist:
                        messages.warning(request, "خطا: زیرپروژه مرتبط یافت نشد.")
                    except Exception as e:
                        messages.warning(request, f"خطا در ارتباط با زیرپروژه دیگر: {str(e)}")
                else:
                    # No relationship or floating relationship
                    calculate_dates_based_on_relationship(subproject, request.POST)
                    subproject.save()
                
                messages.success(request, "زیرپروژه با موفقیت ایجاد شد.")
                return redirect('creator_project:project_detail', pk=project.id)
            
        except ValueError as e:
            messages.error(request, f"خطا در مقادیر ورودی: {str(e)}")
        except Exception as e:
            print(f"DEBUG: Exception occurred: {str(e)}")
            print(f"DEBUG: Exception type: {type(e)}")
            import traceback
            print(f"DEBUG: Traceback: {traceback.format_exc()}")
            messages.error(request, f"خطا در ایجاد زیرپروژه: {str(e)}")
    
    # For GET requests, show the form
    # Get existing subprojects of this project to show in the relationship field
    existing_subprojects = project.subprojects.all().order_by('sub_project_number')
    
    context = {
        'project': project,
        'subproject': None,  # No existing subproject
        'existing_subprojects': existing_subprojects,
    }
    
    return render(request, 'creator_subproject/subproject_form.html', context)

@login_required
def subproject_update(request, subproject_id):
    """Update an existing subproject."""
    subproject = get_object_or_404(SubProject, pk=subproject_id)
    project = subproject.project
    
    # Check permissions using the can_modify_project function
    if not can_modify_project(request.user, project):
        return HttpResponseForbidden("شما مجوز دسترسی به این عملیات را ندارید.")
    
    if request.method == 'POST':
        has_contract = request.POST.get('has_contract') == 'true'
        
        try:
            # Update basic fields
            subproject.name = request.POST.get('name', '')
            subproject.sub_project_type = request.POST.get('sub_project_type')
            subproject.sub_project_number = int(request.POST.get('sub_project_number'))
            subproject.is_suportting_charity = request.POST.get('is_suportting_charity')
            
            # Process common fields
            subproject.state = request.POST.get('state')
            subproject.physical_progress = Decimal(request.POST.get('physical_progress', 0))
            subproject.remaining_work = request.POST.get('remaining_work')
            subproject.description = request.POST.get('description', '')
            
            # Set predicted adjustment amount
            predicted_adjustment_amount = request.POST.get('predicted_adjustment_amount')
            if predicted_adjustment_amount and predicted_adjustment_amount.strip():
                try:
                    # Remove commas and any other non-numeric characters except decimal point
                    cleaned_amount = ''.join(c for c in predicted_adjustment_amount if c.isdigit() or c == '.')
                    if cleaned_amount:
                        subproject.predicted_adjustment_amount = Decimal(cleaned_amount)
                    else:
                        subproject.predicted_adjustment_amount = Decimal('0')
                except (ValueError, InvalidOperation):
                    subproject.predicted_adjustment_amount = Decimal('0')
            else:
                subproject.predicted_adjustment_amount = Decimal('0')
            
            # If this is a subproject with contract information
            if has_contract:
                # Parse dates first
                contract_start_date_str = request.POST.get('contract_start_date')
                contract_end_date_str = request.POST.get('contract_end_date')
                
                print(f"DEBUG: Processing contract dates - start: '{contract_start_date_str}', end: '{contract_end_date_str}'")
                
                contract_start_date = parse_jalali_date(contract_start_date_str)
                contract_end_date = parse_jalali_date(contract_end_date_str)
                
                # Set contract dates
                subproject.contract_start_date = contract_start_date
                subproject.contract_end_date = contract_end_date
                
                # Ensure project dates match contract dates immediately
                if contract_start_date and contract_end_date:
                    subproject.start_date = contract_start_date
                    subproject.end_date = contract_end_date
                elif contract_start_date_str and not contract_start_date:
                    messages.warning(request, f"تاریخ شروع قرارداد نامعتبر است: {contract_start_date_str}")
                elif contract_end_date_str and not contract_end_date:
                    messages.warning(request, f"تاریخ پایان قرارداد نامعتبر است: {contract_end_date_str}")
                
                # Set contract fields
                contract_amount = request.POST.get('contract_amount')
                if contract_amount and contract_amount.strip():
                    try:
                        # Remove commas and any other non-numeric characters except decimal point
                        cleaned_amount = ''.join(c for c in contract_amount if c.isdigit() or c == '.')
                        if cleaned_amount:
                            subproject.contract_amount = Decimal(cleaned_amount)
                        else:
                            subproject.contract_amount = None
                    except (ValueError, InvalidOperation):
                        subproject.contract_amount = None
                else:
                    subproject.contract_amount = None
                    
                # Set contract type
                subproject.contract_type = request.POST.get('contract_type')
                subproject.execution_method = request.POST.get('execution_method')
                
                # Set tender type if provided
                subproject.tender_type = request.POST.get('tender_type')
                
                # Set consultant information if applicable
                subproject.has_consultant = request.POST.get('has_consultant', 'ندارد')
                if subproject.has_consultant == 'دارد':
                    subproject.consultant_name = request.POST.get('consultant_name')
                    subproject.consultant_national_id = request.POST.get('consultant_national_id')
                else:
                    # Clear consultant fields if not applicable
                    subproject.consultant_name = None
                    subproject.consultant_national_id = None
                
                # Set contractor information
                subproject.contractor_name = request.POST.get('contractor_name')
                subproject.contractor_id = request.POST.get('contractor_id')
                
                # Set transaction threshold if provided
                subproject.transaction_threshold = request.POST.get('transaction_threshold', 'کوچک')
                
                # Handle adjustment coefficient 
                has_adjustment = request.POST.get('has_adjustment')
                subproject.has_adjustment = has_adjustment
                
                if has_adjustment == 'دارد' and request.POST.get('adjustment_coefficient'):
                    adjustment_coefficient = request.POST.get('adjustment_coefficient')
                    # Remove commas before converting to Decimal
                    adjustment_coefficient = adjustment_coefficient.replace(',', '')
                    adjustment_coefficient_decimal = Decimal(adjustment_coefficient)
                    
                    # Validate adjustment coefficient is not greater than 25
                    if adjustment_coefficient_decimal > 25:
                        messages.error(request, "درصد افزایش قرارداد نمی‌تواند بیشتر از 25 درصد باشد.")
                        return redirect('creator_subproject:subproject_update', subproject_id=subproject.id)
                    
                    subproject.adjustment_coefficient = adjustment_coefficient_decimal
                else:
                    subproject.adjustment_coefficient = 0
            else:
                # Without contract information, use relationship system
                # Relationship Type: After, Start With, Before, End With
                
                # Clear contract info if not using contract anymore
                subproject.contract_start_date = None
                subproject.contract_end_date = None
                subproject.contract_amount = None
                subproject.contract_type = None
                subproject.execution_method = None
                subproject.has_adjustment = 'ندارد'
                subproject.adjustment_coefficient = 0
                
                # Set imagenary fields
                imagenary_duration = request.POST.get('imagenary_duration')
                if imagenary_duration and imagenary_duration.strip():
                    try:
                        subproject.imagenary_duration = int(imagenary_duration)
                    except ValueError:
                        subproject.imagenary_duration = None
                else:
                    subproject.imagenary_duration = None
                
                imagenrary_cost = request.POST.get('imagenrary_cost')
                if imagenrary_cost and imagenrary_cost.strip():
                    try:
                        # Remove commas and any other non-numeric characters except decimal point
                        cleaned_cost = ''.join(c for c in imagenrary_cost if c.isdigit() or c == '.')
                        if cleaned_cost:
                            cost_decimal = Decimal(cleaned_cost)
                            # Check if the value is within valid range for DECIMAL(15,2)
                            max_value = Decimal('9999999999999.99')
                            if cost_decimal > max_value:
                                messages.error(request, f"مبلغ هزینه تخمینی خیلی بزرگ است. حداکثر مقدار مجاز: {max_value:,} ریال")
                                return redirect('creator_subproject:subproject_update', subproject_id=subproject.id)
                            subproject.imagenrary_cost = cost_decimal
                        else:
                            subproject.imagenrary_cost = None
                    except (ValueError, InvalidOperation) as e:
                        messages.error(request, f"فرمت مبلغ هزینه تخمینی نامعتبر است: {imagenrary_cost}")
                        return redirect('creator_subproject:subproject_update', subproject_id=subproject.id)
                else:
                    subproject.imagenrary_cost = None
                
                # Set cost calculation method
                cost_calculation_method = request.POST.get('cost_calculation_method', '')
                subproject.cost_calculation_method = cost_calculation_method
                
                # Save the instance first to ensure we have a primary key
                subproject.save()
                
                # Now handle relationships and calculate dates after saving
                related_id = request.POST.get('related_subproject')
                relationship_type = request.POST.get('relationship_type')
                
                if related_id and related_id != 'floating' and relationship_type:
                    try:
                        related_subproject = SubProject.objects.get(id=int(related_id))
                        subproject.related_subproject = related_subproject
                        subproject.relationship_type = relationship_type
                        subproject.relationship_delay = int(request.POST.get('relationship_delay', 0) or 0)
                        
                        # Calculate dates based on relationship
                        calculate_dates_based_on_relationship(subproject, request.POST, related_subproject)
                        
                        # Save again with relationship and dates
                        subproject.save()
                    except (ValueError, SubProject.DoesNotExist):
                        messages.warning(request, "زیرپروژه مرتبط یافت نشد.")
                else:
                    # Calculate dates normally without relationship
                    calculate_dates_based_on_relationship(subproject, request.POST)
                    subproject.save()
            
            # Set the current user as the updater
            subproject._current_user = request.user
            
            # Save the subproject
            subproject.save()
                
            # Reset project approval status
            project.is_submitted = False
            project.is_expert_approved = False
            project.is_approved = False
            project.save()
                
            messages.success(request, "زیرپروژه با موفقیت به‌روزرسانی شد.")
            return redirect('creator_subproject:subproject_detail', pk=subproject.id)
        except Exception as e:
            messages.error(request, f"خطا در به‌روزرسانی زیرپروژه: {str(e)}")
            return redirect('creator_subproject:subproject_detail', pk=subproject.id)

    context = {
        'subproject': subproject,
        'project': subproject.project,
        'existing_subprojects': subproject.project.subprojects.exclude(id=subproject.id).order_by('sub_project_number'),
    }
    return render(request, 'creator_subproject/subproject_update_form.html', context)

@login_required
def subproject_delete(request, pk):
    subproject = get_object_or_404(SubProject, pk=pk)
    project = subproject.project

    # Use the can_modify_project function for permission check
    if not can_modify_project(request.user, project):
        return HttpResponseForbidden("شما مجوز دسترسی به این عملیات را ندارید.")

    # Placeholder for actual implementation
    return render(request, 'creator_subproject/subproject_confirm_delete.html', {'subproject': subproject})

@login_required
def submit_subproject(request, pk):
    """Submit subproject for approval"""
    subproject = get_object_or_404(SubProject, pk=pk)
    project = subproject.project
    
    # Check if user is authorized using the can_modify_project function
    if not can_modify_project(request.user, project):
        messages.error(request, 'شما مجاز به انجام این عملیات نیستید.')
        return redirect('creator_subproject:subproject_detail', pk=pk)
    
    # Update parent project status instead
    if not project.is_submitted:
        project.is_submitted = True
        project.save(update_fields=['is_submitted'])
        messages.success(request, 'پروژه با موفقیت ارسال شد.')
    else:
        messages.info(request, 'پروژه قبلاً ارسال شده است.')
    
    return redirect('creator_subproject:subproject_detail', pk=pk)

@login_required
def approve_subproject(request, pk):
    """Approve subproject"""
    subproject = get_object_or_404(SubProject, pk=pk)
    
    # Check if user is authorized
    if not (request.user.is_admin or request.user.is_ceo or request.user.is_chief_executive or request.user.is_expert):
        messages.error(request, 'شما مجاز به انجام این عملیات نیستید.')
        return redirect('creator_subproject:subproject_detail', pk=pk)
    
    # Update parent project status instead
    project = subproject.project
    if project.is_submitted and not project.is_approved:
        project.is_approved = True
        project.save(update_fields=['is_approved'])
        
        # Clear rejection comments when project is approved
        from creator_project.models import ProjectRejectionComment
        ProjectRejectionComment.objects.filter(project=project).delete()
        
        messages.success(request, 'پروژه با موفقیت تایید شد.')
    else:
        messages.info(request, 'پروژه قبلاً تایید شده یا هنوز ارسال نشده است.')
    
    return redirect('creator_subproject:subproject_detail', pk=pk)

@login_required
def reject_subproject(request, pk):
    """Reject subproject"""
    subproject = get_object_or_404(SubProject, pk=pk)
    
    # Check if user is authorized
    if not (request.user.is_admin or request.user.is_ceo or request.user.is_chief_executive or request.user.is_expert):
        messages.error(request, 'شما مجاز به انجام این عملیات نیستید.')
        return redirect('creator_subproject:subproject_detail', pk=pk)
    
    # Update parent project status instead
    project = subproject.project
    if project.is_submitted:
        project.is_submitted = False
        project.save(update_fields=['is_submitted'])
        messages.success(request, 'پروژه با موفقیت رد شد.')
    else:
        messages.info(request, 'پروژه هنوز ارسال نشده است.')
    
    return redirect('creator_subproject:subproject_detail', pk=pk)

@login_required
def subproject_financials(request, pk):
    subproject = get_object_or_404(SubProject, pk=pk)

    # Check permissions
    if not (request.user.is_admin or request.user.is_ceo or request.user.is_chief_executive or 
            request.user.is_vice_chief_executive or request.user.is_expert or 
            subproject.created_by == request.user or
            (request.user.is_province_manager and subproject.project.province in request.user.get_assigned_provinces())):
        return HttpResponseForbidden("You don't have permission to view financial details.")

    # Placeholder for actual implementation
    return render(request, 'creator_subproject/subproject_financials.html', {'subproject': subproject})

@login_required
def subproject_add_situation_report(request, pk):
    # This view redirects to the allocation add view 
    # but needs to be maintained for backward compatibility
    return redirect('creator_subproject:add_allocation', subproject_id=pk)

@login_required
def project_situations_list(request, project_id):
    project = get_object_or_404(Project, pk=project_id)

    # Check permissions
    if not (request.user.is_admin or request.user.is_ceo or request.user.is_chief_executive or 
            request.user.is_vice_chief_executive or request.user.is_expert or 
            (request.user.is_province_manager and (
                project.created_by == request.user or 
                project.province in request.user.get_assigned_provinces()
            ))):
        return HttpResponseForbidden("You don't have permission to view this project's situations.")

    situations = ProjectSituation.objects.filter(project=project)

    context = {
        'project': project,
        'situations': situations,
    }

    return render(request, 'creator_subproject/project_situations_list.html', context)

@login_required
def project_situation_create(request, project_id):
    project = get_object_or_404(Project, pk=project_id)

    # Check permissions
    if not (request.user.is_admin or request.user.is_ceo or request.user.is_chief_executive or 
            request.user.is_vice_chief_executive or request.user.is_expert or 
            project.created_by == request.user or
            (request.user.is_province_manager and project.province in request.user.get_assigned_provinces())):
        return HttpResponseForbidden("You don't have permission to add situations to this project.")

    if request.method == 'POST':
        form = ProjectSituationForm(request.POST)
        if form.is_valid():
            situation = form.save(commit=False)
            situation.project = project
            situation.created_by = request.user
            situation.save()

            messages.success(request, "وضعیت پروژه با موفقیت اضافه شد.")
            return redirect('project_situations_list', project_id=project.id)
    else:
        form = ProjectSituationForm()

    context = {
        'form': form,
        'project': project
    }

    return render(request, 'creator_subproject/project_situation_form.html', context)

@login_required
def project_situation_update(request, pk):
    situation = get_object_or_404(ProjectSituation, pk=pk)

    # Check permissions
    if not (request.user.is_admin or request.user.is_ceo or request.user.is_chief_executive or 
            request.user.is_vice_chief_executive or request.user.is_expert or situation.created_by == request.user):
        return HttpResponseForbidden("You don't have permission to update this situation.")

    if request.method == 'POST':
        form = ProjectSituationForm(request.POST, instance=situation)
        if form.is_valid():
            form.save()
            messages.success(request, "وضعیت پروژه با موفقیت به‌روزرسانی شد.")
            return redirect('project_situations_list', project_id=situation.project.id)
    else:
        form = ProjectSituationForm(instance=situation)

    context = {
        'form': form,
        'situation': situation,
        'project': situation.project
    }

    return render(request, 'creator_subproject/project_situation_form.html', context)

@login_required
def project_situation_delete(request, pk):
    situation = get_object_or_404(ProjectSituation, pk=pk)

    # Check permissions
    if not (request.user.is_admin or request.user.is_ceo or request.user.is_chief_executive or 
            request.user.is_vice_chief_executive or situation.created_by == request.user):
        return HttpResponseForbidden("You don't have permission to delete this situation.")

    # Store the project ID for redirecting after deletion
    project_id = situation.project.id

    if request.method == 'POST':
        situation.delete()
        messages.success(request, "وضعیت پروژه با موفقیت حذف شد.")
        return redirect('project_situations_list', project_id=project_id)

    context = {
        'situation': situation,
        'project': situation.project
    }

    return render(request, 'creator_subproject/project_situation_confirm_delete.html', context)

@login_required
def project_situation_toggle_resolved(request, pk):
    situation = get_object_or_404(ProjectSituation, pk=pk)

    # Check permissions
    if not (request.user.is_admin or request.user.is_ceo or request.user.is_chief_executive or 
            request.user.is_vice_chief_executive or request.user.is_expert or situation.created_by == request.user):
        return HttpResponseForbidden("You don't have permission to update this situation.")

    # Toggle the resolved status
    situation.is_resolved = not situation.is_resolved
    situation.save()

    if situation.is_resolved:
        message = "وضعیت به عنوان حل شده علامت‌گذاری شد."
    else:
        message = "وضعیت به عنوان حل نشده علامت‌گذاری شد."

    return JsonResponse({
        'success': True,
        'message': message,
        'is_resolved': situation.is_resolved
    })

@login_required
def allocations(request, subproject_id):
    """View for listing financial documents for a subproject."""
    subproject = get_object_or_404(SubProject, pk=subproject_id)
    
    # Check permissions
    if not (request.user.is_admin or request.user.is_ceo or request.user.is_chief_executive or 
            request.user.is_expert or request.user == subproject.created_by or 
            request.user == subproject.project.created_by):
        raise PermissionDenied
        
    financial_documents = subproject.financial_documents.all().order_by('-created_at')
    
    # Filter functionality
    document_type = request.GET.get('document_type')
    if document_type:
        financial_documents = financial_documents.filter(document_type=document_type)
        
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        financial_documents = financial_documents.filter(
            Q(document_number__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(financial_documents, 20)  # Show 20 documents per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'subproject': subproject,
        'page_obj': page_obj,
        'financial_documents': page_obj,
        'document_types': dict(FINANCIAL_DOCUMENT_TYPES),
        'selected_type': document_type,
        'search_query': search_query,
    }
    
    return render(request, 'creator_subproject/financial_documents.html', context)

@login_required
def situation_reports(request, subproject_id):
    """
    Display a list of all situation reports for a specific subproject.
    """
    subproject = get_object_or_404(SubProject, pk=subproject_id)
    situation_reports = SituationReport.objects.filter(
        subproject=subproject
    ).order_by('-allocation_date')

    # Calculate total payment amount
    total_payment_amount = situation_reports.aggregate(
        total=Sum('payment_amount_field')
    )['total'] or 0

    context = {
        'subproject': subproject,
        'situation_reports': situation_reports,
        'total_payment_amount': total_payment_amount,
    }
    return render(request, 'creator_subproject/situation_reports.html', context)

@login_required
def add_allocation(request, subproject_id):
    """View for adding a new financial document."""
    subproject = get_object_or_404(SubProject, pk=subproject_id)
    
    # Check permissions
    if not (request.user.is_admin or request.user == subproject.created_by):
        raise PermissionDenied
    
    if request.method == 'POST':
        form = FinancialDocumentForm(request.POST, subproject=subproject)
        files_form = DocumentFileForm(request.POST, request.FILES)
        
        if form.is_valid():
            # Create financial document without saving yet
            financial_document = form.save(commit=False)
            financial_document.subproject = subproject
            financial_document.created_by = request.user
            
            # Ensure contractor_submit_date is set to same value as contractor_date
            if hasattr(financial_document, 'contractor_date') and financial_document.contractor_date:
                financial_document.contractor_submit_date = financial_document.contractor_date
            
            # Ensure approval_date is set (use contractor_date if not provided)
            if not financial_document.approval_date and hasattr(financial_document, 'contractor_date'):
                financial_document.approval_date = financial_document.contractor_date
            
            # Document number is auto-generated by the save method in the model
            financial_document.save()
            
            # Handle document files with multiple file upload support
            files = request.FILES.getlist('files')
            for file_obj in files:
                DocumentFile.objects.create(
                    document=financial_document,
                    file=file_obj.read(), # Read binary content
                    filename=file_obj.name,
                    file_mime_type=file_obj.content_type # Store MIME type
                )
            
            messages.success(request, _('سند مالی با موفقیت اضافه شد.'))
            return redirect('creator_subproject:subproject_detail', pk=subproject.id)
    else:
        # Set initial values
        today_jalali = jdatetime.date.today().strftime('%Y/%m/%d')
        form = FinancialDocumentForm(
            subproject=subproject,
            initial={
                'jalali_contractor_date': today_jalali,
                'jalali_approval_date': today_jalali,
            }
        )
        files_form = DocumentFileForm()
    
    context = {
        'form': form,
        'files_form': files_form,
        'subproject': subproject,
        'title': _('افزودن سند مالی جدید'),
    }
    
    return render(request, 'creator_subproject/financial_document_form.html', context)

@login_required
def edit_allocation(request, pk):
    """View for editing a financial document."""
    financial_document = get_object_or_404(FinancialDocument, pk=pk)
    subproject = financial_document.subproject
    
    # Check permissions
    if not (request.user.is_admin or request.user == financial_document.created_by):
        raise PermissionDenied
    
    if request.method == 'POST':
        form = FinancialDocumentForm(request.POST, instance=financial_document, subproject=subproject)
        files_form = DocumentFileForm(request.POST, request.FILES)
        
        if form.is_valid():
            form.save()
            
            # Handle document files
            files = request.FILES.getlist('files')
            for file_obj in files:
                DocumentFile.objects.create(
                    document=financial_document,
                    file=file_obj.read(), # Read binary content
                    filename=file_obj.name,
                    file_mime_type=file_obj.content_type # Store MIME type
                )
            
            messages.success(request, _('سند مالی با موفقیت بروزرسانی شد.'))
            return redirect('creator_subproject:subproject_detail', pk=subproject.id)
    else:
        form = FinancialDocumentForm(instance=financial_document, subproject=subproject)
        files_form = DocumentFileForm()
    
    context = {
        'form': form,
        'files_form': files_form,
        'financial_document': financial_document,
        'subproject': subproject,
        'title': _('ویرایش سند مالی'),
        'document_files': financial_document.documents.all(),
    }
    
    return render(request, 'creator_subproject/financial_document_form.html', context)

@login_required
def delete_allocation(request, pk):
    """View for deleting a financial document."""
    financial_document = get_object_or_404(FinancialDocument, pk=pk)
    subproject = financial_document.subproject
    
    # Check permissions
    if not (request.user.is_admin or request.user == financial_document.created_by):
        raise PermissionDenied
    
    if request.method == 'POST':
        # Delete associated document files first
        # Files are now stored in the database, no need to remove from filesystem
        financial_document.delete()
        messages.success(request, _('سند مالی با موفقیت حذف شد.'))
        return redirect('creator_subproject:subproject_detail', pk=subproject.id)
    
    context = {
        'object': financial_document,
        'subproject': subproject,
        'title': _('حذف سند مالی'),
    }
    
    return render(request, 'creator_subproject/confirm_delete.html', context)

@login_required
def delete_document_file(request, pk):
    """View for deleting a document file."""
    document_file = get_object_or_404(DocumentFile, pk=pk)
    financial_document = document_file.document
    
    # Check permissions
    if not (request.user.is_admin or request.user == financial_document.created_by):
        raise PermissionDenied
    
    if request.method == 'POST':
        document_file.delete()
        messages.success(request, _('فایل با موفقیت حذف شد.'))
        return redirect('creator_subproject:edit_allocation', pk=financial_document.id)
    
    context = {
        'object': document_file,
        'title': _('حذف فایل'),
    }
    
    return render(request, 'creator_subproject/confirm_delete.html', context)

@login_required
def payments(request, subproject_id):
    """
    Display a list of all payments for a specific subproject.
    """
    subproject = get_object_or_404(SubProject, pk=subproject_id)
    
    # Check permissions - admin users should have access
    if not (request.user.is_admin or request.user.is_ceo or request.user.is_chief_executive or 
            request.user.is_expert or request.user == subproject.created_by or 
            request.user == subproject.project.created_by):
        raise PermissionDenied
    
    payments_list = Payment.objects.filter(
        subproject=subproject
    ).order_by('-payment_date')
    
    # Calculate total payment amount
    total_payment_amount = payments_list.aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    context = {
        'subproject': subproject,
        'payments': payments_list,
        'total_payment_amount': total_payment_amount,
    }
    return render(request, 'creator_subproject/payments.html', context)

@login_required
def add_payment(request, subproject_id):
    """
    Add a new payment for a subproject.
    """
    subproject = get_object_or_404(SubProject, pk=subproject_id)
    project = subproject.project

    # Check permissions - admin users should have access
    if not (request.user.is_admin or request.user == subproject.created_by):
        raise PermissionDenied

    if request.method == 'POST':
        form = PaymentForm(request.POST, subproject=subproject)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.subproject = subproject
            payment.created_by = request.user
            
            # Ensure payment_date is set from the cleaned data
            if 'payment_date' in form.cleaned_data:
                payment.payment_date = form.cleaned_data['payment_date']
            
            payment.save()

            # Reset project approval status if user is province manager
            if request.user.is_province_manager:
                project.is_submitted = False
                project.is_expert_approved = False
                project.is_approved = False
                project.save()

            messages.success(request, "پرداخت با موفقیت اضافه شد.")
            return redirect('creator_subproject:payments', subproject_id=subproject.id)
        else:
            # Log validation errors for debugging
            print(f"DEBUG: Form validation errors: {form.errors}")
    else:
        # Initialize form with today's date in Jalali format
        import jdatetime
        
        today_jalali = jdatetime.date.today().strftime('%Y/%m/%d')
        initial_data = {
            'jalali_payment_date': today_jalali
        }
        
        form = PaymentForm(initial=initial_data, subproject=subproject)

    context = {
        'form': form,
        'subproject': subproject,
    }
    return render(request, 'creator_subproject/add_payment.html', context)

@login_required
def edit_payment(request, payment_id):
    """
    Edit an existing payment.
    """
    payment = get_object_or_404(Payment, pk=payment_id)
    subproject = payment.subproject
    project = subproject.project

    # Check permissions - admin users should have access
    if not (request.user.is_admin or request.user == payment.created_by):
        raise PermissionDenied

    if request.method == 'POST':
        form = PaymentForm(request.POST, instance=payment, subproject=subproject)
        if form.is_valid():
            form.save()

            # Reset project approval status if user is province manager
            if request.user.is_province_manager:
                project.is_submitted = False
                project.is_expert_approved = False
                project.is_approved = False
                project.save()

            messages.success(request, "پرداخت با موفقیت به‌روزرسانی شد.")
            return redirect('creator_subproject:payments', subproject_id=subproject.id)
    else:
        form = PaymentForm(instance=payment, subproject=subproject)

    context = {
        'form': form,
        'subproject': subproject,
        'payment': payment,
    }
    return render(request, 'creator_subproject/edit_payment.html', context)

@login_required
def delete_payment(request, payment_id):
    """
    Delete an existing payment.
    """
    payment = get_object_or_404(Payment, pk=payment_id)
    subproject = payment.subproject
    
    if not subproject:
        messages.error(request, "خطا: پرداخت به زیرپروژه متصل نیست.")
        return redirect('dashboard')
    
    # Permission check
    if not (request.user.is_admin or 
            subproject.created_by == request.user or
            (request.user.is_province_manager and subproject.project.province in request.user.get_assigned_provinces())):
        return HttpResponseForbidden("شما اجازه حذف این پرداخت را ندارید.")

    if request.method == 'POST':
        try:
            payment.delete()
            messages.success(request, "پرداخت با موفقیت حذف شد.")
        except Exception as e:
            messages.error(request, f"خطا در حذف پرداخت: {str(e)}")
        return redirect('creator_subproject:payments', subproject_id=subproject.id)

    return render(request, 'creator_subproject/delete_payment.html', {
        'payment': payment,
        'subproject': subproject
    })

# Alias functions for backward compatibility
adjustment_allocations = payments
add_adjustment_allocation = add_payment

@login_required
def get_subproject_dates(request, subproject_id):
    """
    API endpoint to get the start and end dates of a subproject.
    Returns dates in Jalali format (YYYY/MM/DD).
    """
    from django.http import JsonResponse
    from .utils import gregorian_to_jalali
    
    try:
        subproject = SubProject.objects.get(id=subproject_id)
        
        # Convert dates to Jalali format
        start_date = gregorian_to_jalali(subproject.start_date) if subproject.start_date else ''
        end_date = gregorian_to_jalali(subproject.end_date) if subproject.end_date else ''
        
        return JsonResponse({
            'success': True,
            'start_date': start_date,
            'end_date': end_date,
        })
    except SubProject.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Subproject not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def get_project_gantt_data(request, project_id):
    """
    API endpoint to get updated Gantt chart data for all subprojects in a project.
    Returns calculated dates for subprojects without contracts.
    """
    from django.http import JsonResponse
    from creator_project.models import Project
    import datetime
    from django.utils import timezone
    
    try:
        project = Project.objects.get(id=project_id)
        subprojects = project.subprojects.all()
        
        # Calculate dynamic dates similar to the JavaScript function
        gantt_data = []
        today = timezone.now().date()
        
        # Convert subprojects to list for processing
        subproject_list = []
        for sp in subprojects:
            subproject_list.append({
                'id': sp.id,
                'name': f"{sp.sub_project_type}" + (f" - {sp.name}" if sp.name else ""),
                'start': sp.start_date.strftime('%Y-%m-%d') if sp.start_date else '',
                'end': sp.end_date.strftime('%Y-%m-%d') if sp.end_date else '',
                'progress': float(sp.physical_progress) if sp.physical_progress else 0,
                'relationshipType': sp.relationship_type or '',
                'relatedId': sp.related_subproject.id if sp.related_subproject else None,
                'relationshipDelay': sp.relationship_delay or 0,
                'hasContract': bool(sp.contract_amount),
                'imaginaryDuration': sp.imagenary_duration or 180
            })
        
        # Calculate dynamic dates
        processed_subprojects = calculate_dynamic_dates_backend(subproject_list, today)
        
        return JsonResponse({
            'success': True,
            'subprojects': processed_subprojects
        })
    except Project.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Project not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def calculate_dynamic_dates_backend(subprojects, today):
    """
    Backend implementation of dynamic date calculation for subprojects.
    """
    import copy
    import datetime
    
    processed_subprojects = copy.deepcopy(subprojects)
    
    # First pass: Handle floating subprojects and those with contracts
    for sp in processed_subprojects:
        if sp['hasContract']:
            # Keep original dates for subprojects with contracts, but validate them
            if not sp['start'] or not sp['end']:
                # Set default dates even for contract subprojects if dates are missing
                sp['start'] = today.strftime('%Y-%m-%d')
                sp['end'] = (today + datetime.timedelta(days=sp['imaginaryDuration'])).strftime('%Y-%m-%d')
        elif sp['relationshipType'] == 'شناور' or not sp['relatedId'] or not sp['relationshipType']:
            # Floating subprojects or those without relationships start from today
            start_date = today
            end_date = start_date + datetime.timedelta(days=sp['imaginaryDuration'])
            
            sp['start'] = start_date.strftime('%Y-%m-%d')
            sp['end'] = end_date.strftime('%Y-%m-%d')
        else:
            # Clear any existing dates for subprojects that will be calculated based on relationships
            sp['start'] = ""
            sp['end'] = ""
    
    # Multiple passes to resolve dependencies
    max_iterations = 10
    changed = True
    
    while changed and max_iterations > 0:
        changed = False
        max_iterations -= 1
        
        for sp in processed_subprojects:
            if sp['hasContract'] or sp['relationshipType'] == 'شناور' or not sp['relatedId'] or not sp['relationshipType']:
                continue  # Skip if has contract, floating, or no relationship
            
            # Find related subproject
            related_sp = None
            for rsp in processed_subprojects:
                if rsp['id'] == sp['relatedId']:
                    related_sp = rsp
                    break
            
            if not related_sp:
                continue
                
            if not related_sp['start'] or not related_sp['end']:
                continue  # Skip if related subproject doesn't have dates yet
            
            related_start = datetime.datetime.strptime(related_sp['start'], '%Y-%m-%d').date()
            related_end = datetime.datetime.strptime(related_sp['end'], '%Y-%m-%d').date()
            delay = sp['relationshipDelay']
            
            if sp['relationshipType'] == 'بعد از':  # After - sp starts when related ends
                new_start = related_end + datetime.timedelta(days=delay)
                new_end = new_start + datetime.timedelta(days=sp['imaginaryDuration'])
            elif sp['relationshipType'] == 'قبل از':  # Before - sp ends when related starts
                new_end = related_start - datetime.timedelta(days=delay)
                new_start = new_end - datetime.timedelta(days=sp['imaginaryDuration'])
            elif sp['relationshipType'] == 'شروع با':  # Start with - sp starts with related
                new_start = related_start + datetime.timedelta(days=delay)
                new_end = new_start + datetime.timedelta(days=sp['imaginaryDuration'])
            elif sp['relationshipType'] == 'پایان با':  # End with - sp ends with related
                new_end = related_end + datetime.timedelta(days=delay)
                new_start = new_end - datetime.timedelta(days=sp['imaginaryDuration'])
            else:
                continue
            
            new_start_str = new_start.strftime('%Y-%m-%d')
            new_end_str = new_end.strftime('%Y-%m-%d')
            
            if sp['start'] != new_start_str or sp['end'] != new_end_str:
                sp['start'] = new_start_str
                sp['end'] = new_end_str
                changed = True
    
    return processed_subprojects

@login_required
def subproject_gallery(request, pk):
    """View gallery images for a subproject."""
    subproject = get_object_or_404(SubProject, id=pk)
    images = subproject.gallery_images.all()
    
    # Convert binary images to base64 for HTML rendering
    image_data = []
    for img in images:
        try:
            # Validate image data
            if not img.image:
                print(f"Warning: No image data for image ID {img.id}")
                continue
            
            # Ensure image is bytes
            if not isinstance(img.image, bytes):
                print(f"Warning: Image data for ID {img.id} is not in bytes format")
                continue
            
            # Convert binary to base64 for HTML img tag
            base64_image = base64.b64encode(img.image).decode('utf-8')
            
            # Validate base64 encoding
            if not base64_image:
                print(f"Warning: Failed to encode image ID {img.id}")
                continue
            
            image_data.append({
                'id': img.id,
                'title': img.title or f'تصویر {img.id}',
                'description': img.description or '',
                'mime_type': img.image_mime_type or 'image/jpeg',
                'base64_image': base64_image
            })
        except Exception as e:
            print(f"Error processing image {img.id}: {e}")
    
    # Log total images processed
    print(f"Total images processed: {len(image_data)}")
    
    context = {
        'subproject': subproject,
        'images': image_data,
    }
    
    return render(request, 'creator_subproject/subproject_gallery.html', context)

@login_required
def upload_gallery_image(request, subproject_id):
    """Upload a new image to the subproject gallery."""
    subproject = get_object_or_404(SubProject, id=subproject_id)
    
    # Check if user has permission to edit this subproject
    if not (request.user.is_admin or request.user.is_ceo or request.user.is_chief_executive or 
            request.user.is_expert or subproject.created_by == request.user or
            (request.user.is_province_manager and subproject.project.province in request.user.get_assigned_provinces())):
        messages.error(request, 'شما اجازه دسترسی به این بخش را ندارید.')
        return redirect('creator_subproject:subproject_detail', pk=subproject.id)
    
    if request.method == 'POST':
        form = SubProjectGalleryImageForm(request.POST, request.FILES)
        if form.is_valid():
            # Read the uploaded file as binary
            uploaded_file = request.FILES['image']
            binary_data = uploaded_file.read()
            
            gallery_image = SubProjectGalleryImage(
                subproject=subproject,
                image=binary_data,
                image_mime_type=uploaded_file.content_type or 'image/jpeg',
                title=form.cleaned_data.get('title'),
                description=form.cleaned_data.get('description')
            )
            gallery_image.save()
            
            messages.success(request, 'تصویر با موفقیت آپلود شد.')
            return redirect('creator_subproject:subproject_gallery', pk=subproject.id)
    else:
        form = SubProjectGalleryImageForm()
    
    context = {
        'subproject': subproject,
        'form': form,
    }
    return render(request, 'creator_subproject/upload_gallery_image.html', context)

@login_required
def delete_gallery_image(request, image_id):
    """Delete a gallery image."""
    image = get_object_or_404(SubProjectGalleryImage, id=image_id)
    subproject = image.subproject
    
    # Check if user has permission to delete this image
    if not (request.user.is_admin or request.user.is_ceo or request.user.is_chief_executive or 
            request.user.is_expert or subproject.created_by == request.user or
            (request.user.is_province_manager and subproject.project.province in request.user.get_assigned_provinces())):
        messages.error(request, 'شما اجازه دسترسی به این بخش را ندارید.')
        return redirect('creator_subproject:subproject_gallery', pk=subproject.id)
    
    if request.method == 'POST':
        image.delete()
        messages.success(request, 'تصویر با موفقیت حذف شد.')
    
    return redirect('creator_subproject:subproject_gallery', pk=subproject.id)

@login_required
def financial_documents(request, subproject_id):
    """
    Display a list of all financial documents for a specific subproject.
    """
    subproject = get_object_or_404(SubProject, pk=subproject_id)
    
    # Check permissions - admin users should have access
    if not (request.user.is_admin or request.user.is_ceo or request.user.is_chief_executive or 
            request.user.is_expert or request.user == subproject.created_by or 
            request.user == subproject.project.created_by or
            (request.user.is_province_manager and subproject.project.province in request.user.get_assigned_provinces())):
        raise PermissionDenied
    
    documents = FinancialDocument.objects.filter(
        subproject=subproject
    ).order_by('-approval_date')

    # Calculate total approved amount
    total_approved_amount = documents.aggregate(
        total=Sum('approved_amount')
    )['total'] or 0

    context = {
        'subproject': subproject,
        'documents': documents,
        'total_approved_amount': total_approved_amount,
    }
    return render(request, 'creator_subproject/financial_documents.html', context)

@login_required
def add_financial_document(request, subproject_id):
    """
    Add a new financial document for a subproject.
    """
    subproject = get_object_or_404(SubProject, pk=subproject_id)
    project = subproject.project

    # Check permissions - admin users should have access
    if not (request.user.is_admin or request.user == subproject.created_by):
        raise PermissionDenied

    if request.method == 'POST':
        form = FinancialDocumentForm(request.POST, request.FILES, subproject=subproject)
        if form.is_valid():
            document = form.save(commit=False)
            document.subproject = subproject
            document.created_by = request.user
            document.save()

            # Handle multiple file uploads
            files = request.FILES.getlist('files')
            for file_obj in files:
                DocumentFile.objects.create(
                    document=document,
                    file=file_obj.read(), # Read binary content
                    filename=file_obj.name,
                    file_mime_type=file_obj.content_type # Store MIME type
                )

            # Reset project approval status if user is province manager
            if request.user.is_province_manager:
                project.is_submitted = False
                project.is_expert_approved = False
                project.is_approved = False
                project.save()

            messages.success(request, "سند مالی با موفقیت اضافه شد.")
            return redirect('creator_subproject:financial_documents', subproject_id=subproject.id)
        else:
            # Log validation errors for debugging
            print(f"DEBUG: Form validation errors: {form.errors}")
    else:
        # Initialize form with today's date in Jalali format
        import jdatetime
        
        today_jalali = jdatetime.date.today().strftime('%Y/%m/%d')
        initial_data = {
            'jalali_contractor_date': today_jalali,
            'jalali_approval_date': today_jalali
        }
        
        form = FinancialDocumentForm(initial=initial_data, subproject=subproject)

    context = {
        'form': form,
        'subproject': subproject,
    }
    return render(request, 'creator_subproject/add_financial_document.html', context)

@login_required
def edit_financial_document(request, document_id):
    """
    Edit an existing financial document.
    """
    document = get_object_or_404(FinancialDocument, pk=document_id)
    subproject = document.subproject
    project = subproject.project

    # Check permissions - admin users should have access
    if not (request.user.is_admin or request.user == document.created_by):
        raise PermissionDenied

    if request.method == 'POST':
        form = FinancialDocumentForm(request.POST, request.FILES, instance=document, subproject=subproject)
        if form.is_valid():
            form.save()

            # Handle multiple file uploads
            files = request.FILES.getlist('files')
            for file_obj in files:
                DocumentFile.objects.create(
                    document=document,
                    file=file_obj.read(), # Read binary content
                    filename=file_obj.name,
                    file_mime_type=file_obj.content_type # Store MIME type
                )

            # Reset project approval status if user is province manager
            if request.user.is_province_manager:
                project.is_submitted = False
                project.is_expert_approved = False
                project.is_approved = False
                project.save()

            messages.success(request, "سند مالی با موفقیت به‌روزرسانی شد.")
            return redirect('creator_subproject:financial_documents', subproject_id=subproject.id)
    else:
        form = FinancialDocumentForm(instance=document, subproject=subproject)

    context = {
        'form': form,
        'subproject': subproject,
        'document': document,
    }
    return render(request, 'creator_subproject/edit_financial_document.html', context)

@login_required
def delete_financial_document(request, document_id):
    """
    Delete an existing financial document.
    """
    document = get_object_or_404(FinancialDocument, pk=document_id)
    subproject = document.subproject
    
    if not subproject:
        messages.error(request, "خطا: سند مالی به زیرپروژه متصل نیست.")
        return redirect('dashboard')
    
    # Permission check
    if not (request.user.is_admin or 
            subproject.created_by == request.user or
            (request.user.is_province_manager and subproject.project.province in request.user.get_assigned_provinces())):
        return HttpResponseForbidden("شما اجازه حذف این سند مالی را ندارید.")

    # Check if any other documents reference this one
    referencing_documents = FinancialDocument.objects.filter(related_document=document)
    if referencing_documents.exists():
        messages.error(request, "این سند مالی توسط اسناد دیگر استفاده می‌شود و نمی‌تواند حذف شود.")
        return redirect('creator_subproject:financial_documents', subproject_id=subproject.id)

    # Check if any payments reference this document
    referencing_payments = Payment.objects.filter(related_document=document)
    if referencing_payments.exists():
        messages.error(request, "این سند مالی توسط پرداختی‌ها استفاده می‌شود و نمی‌تواند حذف شود.")
        return redirect('creator_subproject:financial_documents', subproject_id=subproject.id)

    if request.method == 'POST':
        try:
            # Files are now stored in the database, no need to remove from filesystem
            # The CASCADE delete on DocumentFile foreign key handles database deletion
            document.delete()
            messages.success(request, "سند مالی با موفقیت حذف شد.")
        except Exception as e:
            messages.error(request, f"خطا در حذف سند مالی: {str(e)}")
        return redirect('creator_subproject:financial_documents', subproject_id=subproject.id)

    return render(request, 'creator_subproject/delete_financial_document.html', {
        'document': document,
        'subproject': subproject
    })

@login_required
def financial_ledger(request, subproject_id):
    """
    Display financial ledger (کاردکس مالی) for a specific subproject.
    Combines financial documents with their related payments.
    """
    subproject = get_object_or_404(SubProject, pk=subproject_id)
    
    # Check permissions - admin users should have access
    if not (request.user.is_admin or request.user.is_ceo or request.user.is_chief_executive or 
            request.user.is_expert or request.user == subproject.created_by or 
            request.user == subproject.project.created_by or
            (request.user.is_province_manager and subproject.project.province in request.user.get_assigned_provinces())):
        raise PermissionDenied
    
    # Get all financial documents for this subproject
    documents = FinancialDocument.objects.filter(
        subproject=subproject
    ).order_by('-approval_date')
    
    # Create ledger entries combining documents with payments
    ledger_entries = []
    
    for document in documents:
        # Get payments for this document
        payments = Payment.objects.filter(
            related_document=document
        ).order_by('-payment_date')
        
        # Get total payments for this document
        total_payments = payments.aggregate(total=Sum('amount'))['total'] or 0
        
        # Get latest payment date
        latest_payment_date = payments.first().payment_date if payments.exists() else None
        
        # Calculate approval time period in days
        approval_time_period = None
        if document.contractor_submit_date and document.approval_date:
            approval_time_period = (document.approval_date - document.contractor_submit_date).days
        
        # Calculate payment time period in days
        payment_time_period = None
        if document.approval_date and latest_payment_date:
            payment_time_period = (latest_payment_date - document.approval_date).days
        
        # Calculate deduction amount (مبلغ کسورات)
        deduction_amount = document.approved_amount - total_payments
        
        # Calculate deduction percentage (درصد کسورات)
        deduction_percentage = 0
        if document.approved_amount > 0:
            deduction_percentage = (deduction_amount / document.approved_amount) * 100
        
        ledger_entry = {
            'document': document,
            'total_payments': total_payments,
            'latest_payment_date': latest_payment_date,
            'approval_time_period': approval_time_period,
            'payment_time_period': payment_time_period,
            'deduction_amount': deduction_amount,
            'deduction_percentage': deduction_percentage,
        }
        ledger_entries.append(ledger_entry)
    
    # Calculate totals
    total_approved_amount = sum(entry['document'].approved_amount for entry in ledger_entries)
    total_payments_amount = sum(entry['total_payments'] for entry in ledger_entries)
    total_deduction_amount = sum(entry['deduction_amount'] for entry in ledger_entries)
    
    # Calculate overall deduction percentage
    overall_deduction_percentage = 0
    if total_approved_amount > 0:
        overall_deduction_percentage = (total_deduction_amount / total_approved_amount) * 100

    context = {
        'subproject': subproject,
        'ledger_entries': ledger_entries,
        'total_approved_amount': total_approved_amount,
        'total_payments_amount': total_payments_amount,
        'total_deduction_amount': total_deduction_amount,
        'overall_deduction_percentage': overall_deduction_percentage,
    }
    return render(request, 'creator_subproject/financial_ledger.html', context)

@login_required
def serve_document_file(request, pk):
    """
    Serve a document file directly from the database.
    """
    document_file = get_object_or_404(DocumentFile, pk=pk)
    
    # Check permissions (e.g., if user has access to the subproject)
    # For now, let's assume if they can access the URL, they can view the file.
    # More granular permissions can be added here if needed.

    response = HttpResponse(document_file.file, content_type=document_file.file_mime_type)
    response['Content-Disposition'] = f'attachment; filename="{document_file.filename}"'
    return response
