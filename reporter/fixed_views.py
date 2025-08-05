# Copy and paste all the content from views.py, making sure it's properly indented
# Apply category filter if provided
if category_filter:
    if category_filter == 'financial':
        financial_fields = ['budget', 'spent_amount', 'financial_progress']
        project_updates = project_updates.filter(field_name__in=financial_fields)
        subproject_updates = subproject_updates.filter(field_name__in=financial_fields)
    elif category_filter == 'status':
        status_fields = ['status', 'state', 'is_approved', 'is_submitted']
        project_updates = project_updates.filter(field_name__in=status_fields)
        subproject_updates = subproject_updates.filter(field_name__in=status_fields)
    elif category_filter == 'progress':
        progress_fields = ['physical_progress', 'progress', 'completion_status']
        project_updates = project_updates.filter(field_name__in=progress_fields)
        subproject_updates = subproject_updates.filter(field_name__in=progress_fields)
