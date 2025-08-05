from django.contrib import admin
from django.utils.html import format_html
from .models import (
    SubProject, FinancialDocument, Payment, 
    DocumentFile, SituationReport, 
    ProjectSituation, AdjustmentSituationReport
)
from django.contrib import messages

@admin.register(SubProject)
class SubProjectAdmin(admin.ModelAdmin):
    list_display = (
        'project', 
        'sub_project_type', 
        'sub_project_number', 
        'state', 
        'physical_progress'
    )
    list_filter = ('state', 'sub_project_type')
    search_fields = ('project__name', 'sub_project_type')
    readonly_fields = ('created_by', 'created_at', 'updated_at', 'get_final_contract_amount')
    
    def get_final_contract_amount(self, obj):
        if obj.final_contract_amount is not None:
            return f"{obj.final_contract_amount:,} IRR"
        return "-"
    get_final_contract_amount.short_description = "Final Contract Amount"

@admin.register(FinancialDocument)
class FinancialDocumentAdmin(admin.ModelAdmin):
    list_display = (
        'subproject', 
        'document_type', 
        'document_number', 
        'contractor_amount_display', 
        'approved_amount_display', 
        'approval_date', 
        'created_by'
    )
    list_filter = ('document_type', 'approval_date', 'created_at')
    search_fields = ('subproject__project__name', 'subproject__sub_project_type', 'document_number', 'description')
    readonly_fields = ('created_at', 'updated_at', 'created_by')
    ordering = ('-created_at',)
    actions = ['delete_selected_documents']
    
    def contractor_amount_display(self, obj):
        return f"{obj.contractor_amount:,} IRR" if obj.contractor_amount else "N/A"
    contractor_amount_display.short_description = 'Contractor Amount'
    
    def approved_amount_display(self, obj):
        return f"{obj.approved_amount:,} IRR" if obj.approved_amount else "N/A"
    approved_amount_display.short_description = 'Approved Amount'
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def delete_selected_documents(self, request, queryset):
        """
        Custom action to delete selected financial documents with confirmation
        """
        # Count the number of documents to be deleted
        total_count = queryset.count()
        
        # Perform the deletion
        deleted_count, _ = queryset.delete()
        
        # Provide feedback
        self.message_user(
            request, 
            f"Successfully deleted {deleted_count} financial document(s).", 
            messages.SUCCESS
        )
    delete_selected_documents.short_description = "حذف اسناد مالی انتخاب شده"

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'subproject', 
        'amount_display', 
        'related_document', 
        'payment_date', 
        'created_by'
    )
    list_filter = ('payment_date', 'created_at')
    search_fields = ('subproject__project__name', 'subproject__sub_project_type', 'description')
    readonly_fields = ('created_at', 'updated_at', 'created_by')
    ordering = ('-payment_date',)
    
    def amount_display(self, obj):
        return f"{obj.amount:,} IRR" if obj.amount else "N/A"
    amount_display.short_description = 'Payment Amount'
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(SituationReport)
class SituationReportAdmin(admin.ModelAdmin):
    list_display = (
        'subproject', 
        'payment_amount_display', 
        'report_number', 
        'allocation_type', 
        'allocation_date'
    )
    list_filter = ('allocation_type', 'allocation_date')
    search_fields = ('subproject__id', 'subproject__name', 'subproject__project__name')
    ordering = ('-allocation_date',)
    
    def payment_amount_display(self, obj):
        return f"{obj.payment_amount_field:,} IRR" if obj.payment_amount_field else "N/A"
    payment_amount_display.short_description = 'Payment Amount'
