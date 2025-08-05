from django import forms
from .models import ProjectReview, SubProjectReview

class ProjectReviewForm(forms.ModelForm):
    """Form for reviewing projects"""
    class Meta:
        model = ProjectReview
        fields = ['is_approved', 'technical_score', 'financial_score', 'schedule_score', 'scope_score', 'comments']
        labels = {
            'is_approved': 'آیا پروژه را تأیید می‌کنید؟',
            'technical_score': 'امتیاز فنی',
            'financial_score': 'امتیاز مالی',
            'schedule_score': 'امتیاز زمان‌بندی',
            'scope_score': 'امتیاز محدوده',
            'comments': 'توضیحات'
        }
        widgets = {
            'is_approved': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'technical_score': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'financial_score': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'schedule_score': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'scope_score': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

class SubProjectReviewForm(forms.ModelForm):
    """Form for reviewing subprojects"""
    class Meta:
        model = SubProjectReview
        fields = ['is_approved', 'technical_score', 'financial_score', 'schedule_score', 'execution_score', 'comments']
        labels = {
            'is_approved': 'آیا زیرپروژه را تأیید می‌کنید؟',
            'technical_score': 'امتیاز فنی',
            'financial_score': 'امتیاز مالی',
            'schedule_score': 'امتیاز زمان‌بندی',
            'execution_score': 'امتیاز اجرایی',
            'comments': 'توضیحات'
        }
        widgets = {
            'is_approved': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'technical_score': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'financial_score': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'schedule_score': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'execution_score': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        } 