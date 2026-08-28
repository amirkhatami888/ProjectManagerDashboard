"""JSON snapshot generation for the Program -> Project -> SubProject tree.

Snapshots are self-contained, deterministic dumps that the AI assistant and the
MCP catalog can read as structured "system facts". They are never a substitute
for permission checks: consumers must still scope reads to the user's visible
querysets (see .permissions) before exposing snapshot data.

Layout (under ai_assistant/knowledge/snapshots/):
    programs/{pk}.json      program row + nested projects + their subprojects
    projects/{pk}.json      project row + nested subprojects
    subprojects/{pk}.json   subproject row (+ key rolled-up values)
    index.json              lightweight registry keyed by entity and province
"""
import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from django.conf import settings

from creator_program.models import Program
from creator_project.models import Project
from creator_subproject.models import SubProject

SNAPSHOT_DIR = Path(settings.BASE_DIR) / "ai_assistant" / "knowledge" / "snapshots"


def _json_default(value):
    """Unify model field values into JSON-safe primitives."""
    if value is None:
        return None
    if isinstance(value, (Decimal, float, int)):
        return float(value) if isinstance(value, (Decimal, float)) else int(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, (set, tuple)):
        return list(value)
    return str(value)


def _row_fields(obj):
    """Dump every concrete model field as a JSON-safe dict (excludes FKs/relations)."""
    data = {}
    for field in obj._meta.concrete_fields:
        if field.is_relation:
            continue
        name = field.name
        try:
            value = getattr(obj, name, None)
        except Exception:
            value = None
        if callable(value):
            continue
        data[name] = _json_default(value)
    return data


def _subproject_summary(item):
    try:
        total_payments = str(item.total_payment_amount or 0)
    except Exception:
        total_payments = "0"
    try:
        required_credit = str(item.required_credit_for_contract_completion or 0)
    except Exception:
        required_credit = "0"
    try:
        final_contract = str(item.final_contract_amount or 0)
    except Exception:
        final_contract = "0"
    data = _row_fields(item)
    data.update({
        "entity": "subproject",
        "id": item.pk,
        "final_contract_amount_text": final_contract,
        "total_payment_amount_text": total_payments,
        "required_credit_text": required_credit,
    })
    return data


def _project_payload(project, with_subprojects=True):
    data = _row_fields(project)
    data.update({
        "entity": "project",
        "id": project.pk,
        "program_id": getattr(project.program, "pk", None),
        "program_title": getattr(project.program, "title", ""),
    })
    try:
        data["financial_progress"] = project.calculate_financial_progress()
    except Exception:
        data["financial_progress"] = None
    if with_subprojects:
        data["subprojects"] = [
            _subproject_summary(item) for item in project.subprojects.all()
        ]
    return data


def _program_payload(program, with_children=True):
    data = _row_fields(program)
    data.update({"entity": "program", "id": program.pk})
    if with_children:
        data["projects"] = [
            _project_payload(project, with_subprojects=True)
            for project in program.projects.all()
        ]
    return data


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default),
        encoding="utf-8",
    )


def write_program_snapshot(program_id, with_children=True):
    program = Program.objects.get(pk=program_id)
    payload = _program_payload(program, with_children=with_children)
    _write_json(SNAPSHOT_DIR / "programs" / f"{program.pk}.json", payload)
    return payload


def write_project_snapshot(project_id, with_children=True):
    project = Project.objects.get(pk=project_id)
    payload = _project_payload(project, with_subprojects=with_children)
    _write_json(SNAPSHOT_DIR / "projects" / f"{project.pk}.json", payload)
    return payload


def write_subproject_snapshot(subproject_id):
    item = SubProject.objects.get(pk=subproject_id)
    payload = _subproject_summary(item)
    _write_json(SNAPSHOT_DIR / "subprojects" / f"{item.pk}.json", payload)
    return payload


def rebuild_index():
    """Write a lightweight index over all snapshots by entity and province."""
    programs = [
        _program_payload(p, with_children=False)
        for p in Program.objects.all().order_by("title")
    ]
    payload = {
        "generated": datetime.now().isoformat(),
        "programs": programs,
    }
    _write_json(SNAPSHOT_DIR / "index.json", payload)
    return payload


def rebuild_all():
    """Regenerate every snapshot and the index (used by management command)."""
    for program in Program.objects.all():
        write_program_snapshot(program.pk)
    for project in Project.objects.all():
        write_project_snapshot(project.pk)
    for subproject in SubProject.objects.all():
        write_subproject_snapshot(subproject.pk)
    return rebuild_index()
