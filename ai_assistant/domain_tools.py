"""Deterministic, permission-aware tools used by the Persian AI agent."""
from decimal import Decimal

from django.db.models import Q, Sum

from creator_program.models import Program
from creator_project.models import Project, ProjectFinancialAllocation
from creator_subproject.models import (
    AdjustmentSituationReport, FinancialDocument, Payment, SituationReport, SubProject,
)

from .permissions import resolve_visible, visible_programs, visible_projects, visible_subprojects


def _decimal(value):
    try:
        return Decimal(str(value or 0))
    except Exception:
        return Decimal("0")


def _money(value):
    return str(_decimal(value).quantize(Decimal("1")))


def system_overview(user):
    """A small aggregate overview; never exports unrestricted row data."""
    programs = visible_programs(user)
    projects = visible_projects(user)
    subprojects = visible_subprojects(user)
    return {
        "program_count": programs.count(),
        "project_count": projects.count(),
        "subproject_count": subprojects.count(),
        "active_subprojects": subprojects.filter(state="فعال").count(),
        "low_progress_subprojects": subprojects.filter(physical_progress__lt=25).count(),
        "total_project_allocations_rial": _money(
            ProjectFinancialAllocation.objects.filter(
                project__in=projects
            ).aggregate(total=Sum("amount"))["total"]
        ),
        "scope": "فقط داده‌های قابل مشاهده برای کاربر جاری",
    }


def search_site(user, query, entity="all", limit=10):
    """Search identifiers and Persian names inside the user's visible scope."""
    query = str(query or "").strip()
    limit = max(1, min(int(limit or 10), 20))
    if not query:
        return {"query": query, "results": []}

    results = []
    if entity in {"all", "program"}:
        rows = visible_programs(user).filter(
            Q(title__icontains=query) | Q(program_id__icontains=query)
            | Q(city__icontains=query) | Q(province__icontains=query)
        )[:limit]
        results.extend({
            "entity": "program", "id": row.pk, "code": row.program_id,
            "title": row.title, "province": row.province,
        } for row in rows)
    if entity in {"all", "project"}:
        rows = visible_projects(user).filter(
            Q(name__icontains=query) | Q(project_id__icontains=query)
            | Q(city__icontains=query) | Q(province__icontains=query)
        )[:limit]
        results.extend({
            "entity": "project", "id": row.pk, "code": row.project_id,
            "title": row.name, "province": row.province,
        } for row in rows)
    if entity in {"all", "subproject"}:
        rows = visible_subprojects(user).filter(
            Q(name__icontains=query) | Q(project_stage__icontains=query)
            | Q(project__name__icontains=query) | Q(project__project_id__icontains=query)
        )[:limit]
        results.extend({
            "entity": "subproject", "id": row.pk, "code": str(row.sub_project_number),
            "title": row.name or row.project_stage, "project": row.project.name,
            "province": row.project.province,
        } for row in rows)
    return {"query": query, "results": results[:limit], "truncated": len(results) > limit}


def read_program(user, program_id):
    program = resolve_visible(user, Program, program_id)
    projects = visible_projects(user).filter(program=program)
    return {
        "id": program.pk, "program_id": program.program_id, "title": program.title,
        "type": program.program_type, "province": program.province, "city": program.city,
        "license_state": program.license_state, "license_code": program.license_code,
        "address": program.address, "longitude": str(program.longitude or ""),
        "latitude": str(program.latitude or ""), "description": program.description,
        "projects": [{"id": p.pk, "project_id": p.project_id, "name": p.name,
                      "progress": str(p.physical_progress or 0)}
                     for p in projects[:30]],
    }


def read_project(user, project_id):
    project = resolve_visible(user, Project, project_id)
    subprojects = visible_subprojects(user).filter(project=project)
    return {
        "id": project.pk, "project_id": project.project_id, "name": project.name,
        "type": project.project_type, "province": project.province, "city": project.city,
        "status": project.overall_status, "physical_progress": str(project.physical_progress),
        "area_size": str(project.area_size or ""), "notables": str(project.notables or ""),
        "site_area": str(project.site_area or ""), "wall_length": str(project.wall_length or ""),
        "floor": project.floor, "estimated_opening_time": str(project.estimated_opening_time or ""),
        "subprojects": [
            {"id": item.pk, "name": item.name, "number": item.sub_project_number,
             "stage": item.project_stage, "state": item.state,
             "progress": str(item.physical_progress or 0),
             "contract_amount_rial": _money(item.contract_amount),
             "estimated_cost_rial": _money(item.imagenrary_cost)}
            for item in subprojects[:30]
        ],
    }


def read_subproject(user, subproject_id):
    item = resolve_visible(user, SubProject, subproject_id)
    has_contract = bool(item.contract_amount or item.contract_start_date or item.contract_end_date)
    return {
        "id": item.pk, "name": item.name, "project_id": item.project_id,
        "project_name": item.project.name, "number": item.sub_project_number,
        "stage": item.project_stage, "state": item.state,
        "physical_progress": str(item.physical_progress or 0),
        "remaining_work": item.remaining_work, "charity": item.is_suportting_charity,
        "has_contract": has_contract, "contract_type": item.contract_type,
        "contract_start_date": str(item.contract_start_date or ""),
        "contract_end_date": str(item.contract_end_date or ""),
        "contract_amount_rial": _money(item.contract_amount),
        "final_contract_amount_rial": _money(item.final_contract_amount),
        "estimated_duration_days": item.imagenary_duration,
        "estimated_cost_rial": _money(item.imagenrary_cost),
        "contractor": item.contractor_name, "consultant": item.consultant_name,
        "payments_rial": _money(item.total_payment_amount),
        "required_credit_rial": _money(item.required_credit_for_contract_completion),
    }


def validate_subproject(subproject):
    issues = []
    progress = _decimal(subproject.physical_progress)
    if not 0 <= progress <= 100:
        issues.append({"code": "progress_range", "severity": "error",
                       "message": "پیشرفت فیزیکی باید بین صفر و صد باشد."})
    if subproject.start_date and subproject.end_date and subproject.end_date < subproject.start_date:
        issues.append({"code": "date_order", "severity": "error",
                       "message": "تاریخ پایان قبل از تاریخ شروع است."})
    for name in ("contract_amount", "imagenrary_cost", "predicted_adjustment_amount"):
        if _decimal(getattr(subproject, name, 0)) < 0:
            issues.append({"code": "negative_amount", "severity": "error",
                           "field": name, "message": "مبلغ منفی است."})
    has_contract = bool(
        subproject.contract_amount or subproject.contract_start_date
        or subproject.contract_end_date or (
            subproject.contract_type and subproject.contract_type != "فاقد قرارداد"
        )
    )
    if has_contract:
        required = ("contract_start_date", "contract_end_date", "contract_amount", "contract_type")
        missing = [field for field in required if getattr(subproject, field, None) in (None, "")]
        if missing:
            issues.append({"code": "contract_data", "severity": "warning",
                           "fields": missing, "message": "اطلاعات قرارداد ناقص است."})
        if (subproject.contract_start_date and subproject.contract_end_date
                and subproject.contract_end_date < subproject.contract_start_date):
            issues.append({"code": "contract_date_order", "severity": "error",
                           "message": "تاریخ پایان قرارداد قبل از تاریخ شروع قرارداد است."})
    elif not subproject.imagenary_duration or not subproject.imagenrary_cost:
        issues.append({"code": "estimate_data", "severity": "warning",
                       "message": "زیرپروژه فاقد قرارداد، مدت یا هزینه تخمینی کامل ندارد."})
    return {"ok": not any(item["severity"] == "error" for item in issues),
            "subproject_id": subproject.pk, "issues": issues}


def validate_project(user, project_id):
    project = resolve_visible(user, Project, project_id)
    checks = [validate_subproject(item) for item in
              visible_subprojects(user).filter(project=project)]
    issues = []
    if not checks:
        issues.append({"severity": "warning", "message": "پروژه هیچ زیرپروژه‌ای ندارد."})
    errors = sum(1 for check in checks for issue in check["issues"] if issue["severity"] == "error")
    warnings = sum(1 for check in checks for issue in check["issues"] if issue["severity"] == "warning")
    return {"project_id": project.pk, "project_code": project.project_id,
            "ok": errors == 0, "error_count": errors, "warning_count": warnings,
            "project_issues": issues, "subproject_checks": checks}


def financial_audit(user, project_id):
    project = resolve_visible(user, Project, project_id)
    subprojects = visible_subprojects(user).filter(project=project)
    allocations = ProjectFinancialAllocation.objects.filter(project=project)
    documents = FinancialDocument.objects.filter(subproject__in=subprojects)
    payments = Payment.objects.filter(subproject__in=subprojects)
    situations = SituationReport.objects.filter(subproject__in=subprojects)
    adjustments = AdjustmentSituationReport.objects.filter(subproject__in=subprojects)

    allocation_sum = _decimal(allocations.aggregate(total=Sum("amount"))["total"])
    contract_sum = sum((_decimal(item.final_contract_amount) for item in subprojects), Decimal("0"))
    approved_documents = _decimal(documents.aggregate(total=Sum("approved_amount"))["total"])
    direct_payments = _decimal(payments.aggregate(total=Sum("amount"))["total"])
    situation_sum = _decimal(situations.aggregate(total=Sum("payment_amount_field"))["total"])
    adjustment_sum = _decimal(adjustments.aggregate(total=Sum("payment_amount_field"))["total"])
    warnings = []
    if direct_payments and situation_sum and direct_payments != situation_sum:
        warnings.append("جمع پرداخت‌ها با جمع صورت‌وضعیت کارکرد برابر نیست؛ نوع ثبت مالی باید بررسی شود.")
    if approved_documents > contract_sum and contract_sum:
        warnings.append("جمع ناخالص تأییدشده اسناد از مبلغ نهایی قراردادها بیشتر است.")
    if direct_payments > approved_documents and approved_documents:
        warnings.append("جمع پرداخت‌ها از مبلغ اسناد تأییدشده بیشتر است.")
    if contract_sum > allocation_sum:
        warnings.append("مبلغ نهایی قراردادها از کل تخصیص پروژه بیشتر است.")
    return {
        "project_id": project.pk, "project_code": project.project_id,
        "allocation_total_rial": _money(allocation_sum),
        "final_contract_total_rial": _money(contract_sum),
        "approved_documents_total_rial": _money(approved_documents),
        "direct_payments_total_rial": _money(direct_payments),
        "work_situations_total_rial": _money(situation_sum),
        "adjustment_situations_total_rial": _money(adjustment_sum),
        "allocation_minus_contract_rial": _money(allocation_sum - contract_sum),
        "contract_minus_payments_rial": _money(contract_sum - direct_payments),
        "warnings": warnings,
        "calculation_note": "محاسبات قطعی از رکوردهای دیتابیس هستند؛ پیش‌بینی قیمت نیازمند منبع وب و فرضیات زمانی است.",
    }
