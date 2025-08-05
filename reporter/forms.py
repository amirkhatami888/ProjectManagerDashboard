from django import forms
from .models import ProjectReport, SubProjectReport
from creator_project.models import Project
from creator_subproject.models import SubProject

class ProjectReportForm(forms.ModelForm):
    class Meta:
        model = ProjectReport
        fields = ['project', 'title', 'report_type', 'content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 10, 'dir': 'rtl'}),
            'title': forms.TextInput(attrs={'dir': 'rtl'}),
        }
        labels = {
            'project': 'پروژه',
            'title': 'عنوان گزارش',
            'report_type': 'نوع گزارش',
            'content': 'محتوای گزارش',
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(ProjectReportForm, self).__init__(*args, **kwargs)
        
        # Filter projects based on user role
        if user and not user.is_superuser:
            if hasattr(user, 'userprofile') and user.userprofile.role == 'province_manager':
                self.fields['project'].queryset = Project.objects.filter(province=user.userprofile.province)
            else:
                # For other roles, show projects they have access to
                self.fields['project'].queryset = Project.objects.filter(created_by=user)


class SubProjectReportForm(forms.ModelForm):
    class Meta:
        model = SubProjectReport
        fields = ['subproject', 'title', 'report_type', 'content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 10, 'dir': 'rtl'}),
            'title': forms.TextInput(attrs={'dir': 'rtl'}),
        }
        labels = {
            'subproject': 'زیرپروژه',
            'title': 'عنوان گزارش',
            'report_type': 'نوع گزارش',
            'content': 'محتوای گزارش',
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(SubProjectReportForm, self).__init__(*args, **kwargs)
        
        # Filter subprojects based on user role
        if user and not user.is_superuser:
            if hasattr(user, 'userprofile') and user.userprofile.role == 'province_manager':
                # Get projects in user's province
                province_projects = Project.objects.filter(province=user.userprofile.province)
                # Filter subprojects linked to those projects
                self.fields['subproject'].queryset = SubProject.objects.filter(project__in=province_projects)
            else:
                # For other roles, show subprojects they have access to
                user_projects = Project.objects.filter(created_by=user)
                self.fields['subproject'].queryset = SubProject.objects.filter(project__in=user_projects) 