from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User, ExpertProvince, UserProvince
from .forms import CustomUserCreationForm, CustomUserChangeForm

class ExpertProvinceInline(admin.TabularInline):
    model = ExpertProvince
    extra = 1
    verbose_name = _("Expert Province Assignment")
    verbose_name_plural = _("Expert Province Assignments")

class UserProvinceInline(admin.TabularInline):
    model = UserProvince
    extra = 1
    verbose_name = _("Province Assignment")
    verbose_name_plural = _("Province Assignments")

class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User
    
    list_display = ('username', 'email', 'role', 'province', 'get_assigned_provinces', 'is_active')
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'profile_picture')}),
        (_('Role info'), {'fields': ('role', 'province')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role', 'province', 'is_active'),
        }),
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    
    def get_inlines(self, request, obj=None):
        """Add appropriate province inlines based on user role"""
        if obj:
            if obj.role == 'EXPERT':
                return [ExpertProvinceInline]
            elif obj.role in ['PROVINCE_MANAGER', 'VICE_CHIEF_EXECUTIVE']:
                return [UserProvinceInline]
        return []
    
    def get_assigned_provinces(self, obj):
        """Show all assigned provinces for the user"""
        if obj.role == 'EXPERT':
            provinces = list(obj.expert_provinces.values_list('province', flat=True))
        else:
            provinces = list(obj.user_provinces.values_list('province', flat=True))
        
        if provinces:
            return ", ".join(provinces)
        return obj.province or "-"
    get_assigned_provinces.short_description = _("Assigned Provinces")

class ExpertProvinceAdmin(admin.ModelAdmin):
    list_display = ('expert', 'province')
    list_filter = ('province',)
    search_fields = ('expert__username', 'expert__email', 'province')
    autocomplete_fields = ['expert']
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "expert":
            kwargs["queryset"] = User.objects.filter(role='EXPERT')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class UserProvinceAdmin(admin.ModelAdmin):
    list_display = ('user', 'province')
    list_filter = ('province',)
    search_fields = ('user__username', 'user__email', 'province')

# Register your models here
admin.site.register(User, CustomUserAdmin)
admin.site.register(ExpertProvince, ExpertProvinceAdmin)
admin.site.register(UserProvince, UserProvinceAdmin)
