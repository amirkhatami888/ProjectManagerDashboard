"""MCP (Model Context Protocol) server exposing reporter search as tools.

Run with a stdio MCP client:

    python manage.py run_ai_mcp

Each tool re-applies the AI permission scoping per invocation. A "viewer"
string carries the acting user's username so results stay province-scoped; if
no user is supplied the tool may only return results for FULL_ACCESS roles.
"""
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project_dashboard.settings")

import django

django.setup()

from mcp.server.fastmcp import FastMCP  # noqa: E402
from accounts.models import User  # noqa: E402

from . import reporter_tools  # noqa: E402
from .reporter_tools import (  # noqa: E402
    _PROGRAM_TYPES, _LICENSE_STATES, _PROJECT_TYPES, _PROJECT_STATUSES,
    _SUBPROJECT_STAGES, _SUBPROJECT_STATES, _CONTRACT_TYPES, _PROVINCES,
)
from .domain_tools import (  # noqa: E402
    get_program_json_template, get_project_json_template,
    get_subproject_json_template, analyze_program_buildings,
)

mcp = FastMCP("pmd-reporter-search")


def _resolve_user(username):
    if not username:
        return None
    try:
        return User.objects.get(username=username, is_active=True)
    except User.DoesNotExist:
        return None


def _guard_user(user):
    user = user or {}
    username = user.get("username") if isinstance(user, dict) else None
    account = _resolve_user(username)
    if account is None:
        raise PermissionError(
            "کاربر معتبری برای تفکیک دسترسی ارسال نشده است؛ نتیجه فقط برای "
            "نقش‌های دسترسی کامل قابل بازگشت است.")
    return account


_PROGRAM_SEARCH_DOC = (
    "جستجوی طرح با فیلترهای بخش گزارش‌گیر (/reporter/program-search/).\n"
    "گزینه‌های مجاز (فقط از این‌ها استفاده کن؛ مقدار خارج از این فهرست به‌صورت خودکار"
    " به نزدیک‌ترین گزینه تبدیل شده و در option_corrections اعلام می‌شود):\n"
    f"  program_types: {list(_PROGRAM_TYPES)}\n"
    f"  provinces: {list(_PROVINCES)}\n"
    f"  license_states: {list(_LICENSE_STATES)}\n"
)


def _program_search(query="", program_types=None, provinces=None,
                    license_states=None, license_codes=None, from_date="",
                    to_date="", limit: int = 20, viewer: dict = None):
    return reporter_tools.search_programs(
        _guard_user(viewer), query=query, program_types=program_types,
        provinces=provinces, license_states=license_states,
        license_codes=license_codes, from_date=from_date, to_date=to_date,
        limit=limit)


_program_search.__doc__ = _PROGRAM_SEARCH_DOC
mcp.tool(name="program_search")(_program_search)


def _project_search(query="", project_types=None, project_statuses=None,
                    provinces=None, program_types=None, license_states=None,
                    min_physical_progress=None, max_physical_progress=None,
                    min_financial_progress=None, max_financial_progress=None,
                    limit: int = 20, viewer: dict = None):
    return reporter_tools.search_projects(
        _guard_user(viewer), query=query, project_types=project_types,
        project_statuses=project_statuses, provinces=provinces,
        program_types=program_types, license_states=license_states,
        min_physical_progress=min_physical_progress,
        max_physical_progress=max_physical_progress,
        min_financial_progress=min_financial_progress,
        max_financial_progress=max_financial_progress, limit=limit)


_project_search.__doc__ = (
    "جستجوی پروژه با فیلترهای گزارش‌گیر (/reporter/search-history/).\n"
    "گزینه‌های مجاز (فقط از این‌ها استفاده کن؛ مقدار خارج از این فهرست به‌صورت خودکار"
    " به نزدیک‌ترین گزینه تبدیل شده و در option_corrections اعلام می‌شود):\n"
    f"  project_types: {list(_PROJECT_TYPES)}\n"
    f"  project_statuses: {list(_PROJECT_STATUSES)}\n"
    f"  provinces: {list(_PROVINCES)}\n"
    f"  program_types: {list(_PROGRAM_TYPES)}\n"
    f"  license_states: {list(_LICENSE_STATES)}\n"
)
mcp.tool(name="project_search")(_project_search)


def _subproject_search(query="", provinces=None, stages=None, states=None,
                       contract_types=None, min_progress=None,
                       max_progress=None, limit: int = 20, viewer: dict = None):
    return reporter_tools.search_subprojects(
        _guard_user(viewer), query=query, provinces=provinces, stages=stages,
        states=states, contract_types=contract_types,
        min_progress=min_progress, max_progress=max_progress, limit=limit)


_subproject_search.__doc__ = (
    "جستجوی زیرپروژه با نام، مرحله، وضعیت، نوع قرارداد و پیشرفت.\n"
    "گزینه‌های مجاز (فقط از این‌ها استفاده کن؛ مقدار خارج از این فهرست به‌صورت خودکار"
    " به نزدیک‌ترین گزینه تبدیل شده و در option_corrections اعلام می‌شود):\n"
    f"  provinces: {list(_PROVINCES)}\n"
    f"  stages: {list(_SUBPROJECT_STAGES)}\n"
    f"  states: {list(_SUBPROJECT_STATES)}\n"
    f"  contract_types: {list(_CONTRACT_TYPES)}\n"
)
mcp.tool(name="subproject_search")(_subproject_search)


@mcp.tool()
def search_history(search_type: str = "", limit: int = 20, viewer: dict = None):
    u"""فهرست تاریخچه جستجوهای گزارش‌گیر خود کاربر جاری."""
    return reporter_tools.search_history(
        _guard_user(viewer), search_type=search_type, limit=limit)


@mcp.tool()
def get_subproject_json_template(subproject_id: int, viewer: dict = None):
    u"""قالب JSON کامل و پویا برای یک زیرپروژه (به‌صورت لحظه‌ای، بدون ذخیره روی سرور)."""
    return get_subproject_json_template(_guard_user(viewer), subproject_id)


@mcp.tool()
def get_project_json_template(project_id: int, viewer: dict = None):
    u"""قالب JSON کامل و پویا برای یک پروژه به‌همراه همه زیرپروژه‌های داخلش."""
    return get_project_json_template(_guard_user(viewer), project_id)


@mcp.tool()
def get_program_json_template(program_id: int, viewer: dict = None):
    u"""قالب JSON کامل و پویا برای یک طرح به‌همراه همه پروژه‌ها و زیرپروژه‌های داخلش."""
    return get_program_json_template(_guard_user(viewer), program_id)


@mcp.tool()
def analyze_program_buildings(provinces: list, viewer: dict = None, province: str = None):
    u"""پیمایش عمیق همه طرح‌های یک یا چند استان برای یافتن ساختمان‌های نیمه‌کاره (پروژه‌های احداث/تکمیل با پیشرفت کمتر از ۱۰۰٪ یا دارای زیرپروژهٔ تحویل‌نشده). برای «آذربایجان»/«خراسان» بدون صفت هر دو استان متناظر پوشش داده می‌شود."""
    return analyze_program_buildings(_guard_user(viewer), province=province, provinces=provinces)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
