"""Reporter-style search exposed to the AI agent.

These replicate the query semantics of /reporter/program-search/ and
/reporter/search-history/ (project search) as permission-aware, JSON-returning
functions. Every query is scoped to the user's visible querysets, and results
are returned as compact, deterministic dicts the model can cite.
"""
from datetime import datetime

from django.db.models import Q

from reporter.models import SearchHistory

from .domain_tools import _money
from .permissions import visible_programs, visible_projects, visible_subprojects

_PROJECT_TYPES = (
    "احداث", "تکمیل", "محوطه سازی", "دیوار کشی",
    "محوطه سازی و دیوار کشی", "تعمیرات",
    "مشاور فاز یک و دو (طراحی)", "مشاور فاز سه (نظارت)",
)
_PROGRAM_TYPES = (
    "پایگاه امداد جاده‌ای", "پایگاه امداد کوهستانی", "پایگاه امداد دریایی",
    "ساختمان اداری آموزشی درمانی وفرهنگی",
    "پایگاه عملیات پشتیبانی اقماری هوایی", "مولد سازی",
    "سالن چند منظوره/انبار امدادی",
)
_LICENSE_STATES = ("دارد", "ندارد", "دردست اقدام", "قبل از بخش نامه اردیبهشت 91")


def _word_query(fields, query):
    query_filter = Q()
    for word in str(query or "").split():
        word_q = Q()
        for field in fields:
            word_q |= Q(**{f"{field}__icontains": word})
        query_filter |= word_q
    return query_filter


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except ValueError:
        return None


def _validate_choice(values, allowed):
    if isinstance(values, str):
        values = [values]
    return [v for v in (values or []) if v in allowed]


def search_programs(user, query="", program_types=None, provinces=None,
                    license_states=None, license_codes=None, from_date="",
                    to_date="", limit=20):
    """Mirror of /reporter/program-search/ scoped to visible programs."""
    qs = visible_programs(user).order_by("title")
    if query:
        qs = qs.filter(_word_query(
            ("title", "program_id", "province", "city", "program_type",
             "license_state", "license_code"), query))
    if program_types := _validate_choice(program_types, _PROGRAM_TYPES):
        qs = qs.filter(program_type__in=program_types)
    if provinces:
        qs = qs.filter(province__in=provinces)
    if license_states := _validate_choice(license_states, _LICENSE_STATES):
        qs = qs.filter(license_state__in=license_states)
    if license_codes:
        qs = qs.filter(license_code__icontains=license_codes[0])
    if from_date and _parse_date(from_date):
        qs = qs.filter(created_at__date__gte=_parse_date(from_date))
    if to_date and _parse_date(to_date):
        qs = qs.filter(created_at__date__lte=_parse_date(to_date))

    rows = qs[: min(max(int(limit), 1), 50)]
    results = [{
        "id": row.pk, "program_id": row.program_id, "title": row.title,
        "program_type": row.program_type, "province": row.province,
        "city": row.city, "license_state": row.license_state,
        "license_code": row.license_code,
        "opening_date": row.program_opening_date.isoformat()
        if row.program_opening_date else None,
        "project_count": row.projects.count(),
    } for row in rows]
    return {"entity": "program", "query": query, "count": len(results),
            "results": results}


def search_projects(user, query="", project_types=None, project_statuses=None,
                    provinces=None, program_types=None, license_states=None,
                    min_physical_progress=None, max_physical_progress=None,
                    min_financial_progress=None, max_financial_progress=None,
                    limit=20):
    """Mirror of /reporter/search-history/ (project search)."""
    qs = visible_projects(user).select_related("program").order_by("name")
    if query:
        qs = qs.filter(_word_query(
            ("name", "project_id", "province", "city", "project_type",
             "overall_status", "program__title", "program__program_id",
             "program__program_type", "program__license_state",
             "program__license_code", "program__province", "program__city"),
            query))
    if project_types := _validate_choice(project_types, _PROJECT_TYPES):
        qs = qs.filter(project_type__in=project_types)
    if project_statuses:
        qs = qs.filter(overall_status__in=project_statuses)
    if provinces:
        qs = qs.filter(province__in=provinces)
    if program_types := _validate_choice(program_types, _PROGRAM_TYPES):
        qs = qs.filter(program__program_type__in=program_types)
    if license_states := _validate_choice(license_states, _LICENSE_STATES):
        qs = qs.filter(program__license_state__in=license_states)
    if min_physical_progress is not None:
        qs = qs.filter(physical_progress__gte=float(min_physical_progress))
    if max_physical_progress is not None:
        qs = qs.filter(physical_progress__lte=float(max_physical_progress))

    rows = list(qs[: min(max(int(limit), 1), 50)])

    # Financial progress is computed per row, so filter it in Python.
    if min_financial_progress is not None or max_financial_progress is not None:
        low = float(min_financial_progress) if min_financial_progress is not None else None
        high = float(max_financial_progress) if max_financial_progress is not None else None
        rows = [r for r in rows
                if (low is None or r.calculate_financial_progress() >= low)
                and (high is None or r.calculate_financial_progress() <= high)]

    results = [{
        "id": row.pk, "project_id": row.project_id, "name": row.name,
        "project_type": row.project_type, "province": row.province,
        "city": row.city, "overall_status": row.overall_status,
        "physical_progress": float(row.physical_progress or 0),
        "financial_progress": row.calculate_financial_progress(),
        "program_title": row.program.title if row.program_id else None,
        "opening_time": row.estimated_opening_time.isoformat()
        if row.estimated_opening_time else None,
        "subproject_count": row.subprojects.count(),
    } for row in rows]
    return {"entity": "project", "query": query, "count": len(results),
            "results": results}


def search_subprojects(user, query="", provinces=None, stages=None,
                       states=None, contract_types=None,
                       min_progress=None, max_progress=None, limit=20):
    """Direct subproject search (not offered in the reporter UI as a search)."""
    qs = visible_subprojects(user).select_related("project", "project__program")
    if query:
        qs = qs.filter(_word_query(
            ("name", "project_stage", "project__name", "project__project_id",
             "project__province", "project__program__title"), query))
    if provinces:
        qs = qs.filter(project__province__in=provinces)
    if stages:
        qs = qs.filter(project_stage__in=stages)
    if states:
        qs = qs.filter(state__in=states)
    if contract_types:
        qs = qs.filter(contract_type__in=contract_types)
    if min_progress is not None:
        qs = qs.filter(physical_progress__gte=float(min_progress))
    if max_progress is not None:
        qs = qs.filter(physical_progress__lte=float(max_progress))

    rows = qs[: min(max(int(limit), 1), 50)]
    results = [{
        "id": row.pk, "number": row.sub_project_number,
        "name": row.name, "stage": row.project_stage, "state": row.state,
        "physical_progress": float(row.physical_progress or 0),
        "contract_type": row.contract_type,
        "contract_amount_rial": _money(row.contract_amount),
        "final_contract_amount_rial": _money(row.final_contract_amount),
        "estimated_cost_rial": _money(row.imagenrary_cost),
        "required_credit_rial": _money(row.required_credit_for_contract_completion),
        "project_id": row.project_id, "project_name": row.project.name,
        "province": row.project.province,
    } for row in rows]
    return {"entity": "subproject", "query": query, "count": len(results),
            "results": results}


def search_history(user, search_type="", limit=20):
    """List the current user's own reporter search history (never others')."""
    if not user.is_authenticated:
        return {"results": []}
    qs = SearchHistory.objects.filter(user=user)
    if search_type in {t for t, _ in SearchHistory.SEARCH_TYPES}:
        qs = qs.filter(search_type=search_type)
    rows = qs[: min(max(int(limit), 1), 50)]
    return {
        "entity": "search_history",
        "results": [{
            "id": row.pk,
            "query_text": row.query_text,
            "search_type": row.search_type,
            "results_count": row.results_count,
            "timestamp": row.timestamp.isoformat()
            if row.timestamp else None,
            "filters": row.filters or {},
        } for row in rows],
    }
