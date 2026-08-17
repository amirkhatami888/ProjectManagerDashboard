"""Centralized, server-side authorization for assistant tools."""
from django.db.models import Q

from creator_program.models import Program
from creator_project.models import Project
from creator_subproject.models import SubProject


FULL_ACCESS_ROLES = {"ADMIN", "CEO", "CHIEF_EXECUTIVE"}


def accessible_provinces(user):
    if not user.is_authenticated:
        return []
    provinces = list(user.get_assigned_provinces())
    if not provinces and getattr(user, "province", None):
        provinces = [user.province]
    return provinces


def can_read_province(user, province):
    return user.is_authenticated and (
        getattr(user, "role", None) in FULL_ACCESS_ROLES
        or province in accessible_provinces(user)
    )


def can_write_object(user, obj):
    if not user.is_authenticated:
        return False
    province = getattr(obj, "province", None)
    if province is None:
        project = getattr(obj, "project", None)
        province = getattr(project, "province", None)
    if province is None:
        program = getattr(obj, "program", None)
        province = getattr(program, "province", None)
    if getattr(user, "role", None) in FULL_ACCESS_ROLES:
        return True
    if not can_read_province(user, province):
        return False
    # Match the application's existing ownership rule for ordinary users.
    owner = getattr(obj, "created_by", None)
    return getattr(user, "is_province_manager", False) or owner == user


def visible_programs(user):
    qs = Program.objects.all()
    if getattr(user, "role", None) in FULL_ACCESS_ROLES:
        return qs
    return qs.filter(province__in=accessible_provinces(user))


def visible_projects(user):
    qs = Project.objects.select_related("program")
    if getattr(user, "role", None) in FULL_ACCESS_ROLES:
        return qs
    provinces = accessible_provinces(user)
    return qs.filter(Q(province__in=provinces) | Q(program__province__in=provinces)).distinct()


def visible_subprojects(user):
    qs = SubProject.objects.select_related("project", "project__program")
    if getattr(user, "role", None) in FULL_ACCESS_ROLES:
        return qs
    provinces = accessible_provinces(user)
    return qs.filter(
        Q(project__province__in=provinces) | Q(project__program__province__in=provinces)
    ).distinct()


def resolve_visible(user, model, object_id):
    qs = {Program: visible_programs(user), Project: visible_projects(user),
          SubProject: visible_subprojects(user)}.get(model)
    if qs is None:
        raise ValueError("مدل برای ابزار دستیار مجاز نیست.")
    try:
        return qs.get(pk=int(object_id))
    except model.DoesNotExist:
        raise PermissionError("رکورد پیدا نشد یا خارج از محدوده دسترسی شماست.")
