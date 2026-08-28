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


@mcp.tool()
def program_search(query: str = "", program_types=None, provinces=None,
                   license_states=None, license_codes=None, from_date="",
                   to_date="", limit: int = 20, viewer: dict = None):
    u"""جستجوی طرح با فیلترهای بخش گزارش‌گیر (/reporter/program-search/)."""
    return reporter_tools.search_programs(
        _guard_user(viewer), query=query, program_types=program_types,
        provinces=provinces, license_states=license_states,
        license_codes=license_codes, from_date=from_date, to_date=to_date,
        limit=limit)


@mcp.tool()
def project_search(query: str = "", project_types=None, project_statuses=None,
                   provinces=None, program_types=None, license_states=None,
                   min_physical_progress=None, max_physical_progress=None,
                   min_financial_progress=None, max_financial_progress=None,
                   limit: int = 20, viewer: dict = None):
    u"""جستجوی پروژه با فیلترهای گزارش‌گیر (/reporter/search-history/)."""
    return reporter_tools.search_projects(
        _guard_user(viewer), query=query, project_types=project_types,
        project_statuses=project_statuses, provinces=provinces,
        program_types=program_types, license_states=license_states,
        min_physical_progress=min_physical_progress,
        max_physical_progress=max_physical_progress,
        min_financial_progress=min_financial_progress,
        max_financial_progress=max_financial_progress, limit=limit)


@mcp.tool()
def subproject_search(query: str = "", provinces=None, stages=None,
                      states=None, contract_types=None, min_progress=None,
                      max_progress=None, limit: int = 20, viewer: dict = None):
    u"""جستجوی زیرپروژه با نام، مرحله، وضعیت، نوع قرارداد و پیشرفت."""
    return reporter_tools.search_subprojects(
        _guard_user(viewer), query=query, provinces=provinces, stages=stages,
        states=states, contract_types=contract_types,
        min_progress=min_progress, max_progress=max_progress, limit=limit)


@mcp.tool()
def search_history(search_type: str = "", limit: int = 20, viewer: dict = None):
    u"""فهرست تاریخچه جستجوهای گزارش‌گیر خود کاربر جاری."""
    return reporter_tools.search_history(
        _guard_user(viewer), search_type=search_type, limit=limit)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
