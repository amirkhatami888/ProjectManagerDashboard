"""Bounded agent loop with explicit, permission-aware Django tools."""
import json

from .domain_tools import (
    financial_audit, read_program, read_project, read_subproject, search_site,
    project_forecast, system_overview, validate_project,
    get_program_json_template, get_project_json_template,
    get_subproject_json_template, analyze_program_buildings,
)
from .search import tavily_search
from .tools import explain_field
from .js_runner import run_local_js
from .reporter_tools import (
    search_history, search_programs, search_projects, search_subprojects,
    _PROJECT_TYPES, _PROGRAM_TYPES, _LICENSE_STATES, _PROJECT_STATUSES,
    _SUBPROJECT_STAGES, _SUBPROJECT_STATES, _CONTRACT_TYPES, _PROVINCES,
)
from .permissions import visible_programs, visible_projects, visible_subprojects
from creator_program.models import Program
from creator_project.models import Project
from creator_subproject.models import SubProject
import os


def _function(name, description, properties=None, required=None):
    return {"type": "function", "function": {
        "name": name, "description": description,
        "parameters": {"type": "object", "properties": properties or {},
                       "required": required or [], "additionalProperties": False},
    }}


BASE_TOOL_SCHEMAS = [
    _function("system_overview", "خلاصه آماری کل داده‌های قابل مشاهده کاربر"),
    _function("search_site", "جستجوی طرح، پروژه یا زیرپروژه با نام یا کد", {
        "query": {"type": "string"},
        "entity": {"type": "string", "enum": ["all", "program", "project", "subproject"]},
        "limit": {"type": "integer", "minimum": 1, "maximum": 20},
    }, ["query"]),
    _function("read_program", "خواندن جزئیات یک طرح مجاز با شناسه داخلی", {
        "program_id": {"type": "integer"},
    }, ["program_id"]),
    _function("read_project", "خواندن جزئیات یک پروژه مجاز با شناسه داخلی", {
        "project_id": {"type": "integer"},
    }, ["project_id"]),
    _function("read_subproject", "خواندن جزئیات قراردادی و مالی یک زیرپروژه مجاز", {
        "subproject_id": {"type": "integer"},
    }, ["subproject_id"]),
    _function("get_subproject_json_template",
        "بازگشت قالب JSON کامل و پویا برای یک زیرپروژه؛ به‌صورت لحظه‌ای از دیتابیس ساخته می‌شود، روی سرور ذخیره نمی‌شود و به‌طور خودکار آزاد می‌شود", {
        "subproject_id": {"type": "integer"},
    }, ["subproject_id"]),
    _function("get_project_json_template",
        "بازگشت قالب JSON کامل و پویا برای یک پروژه به‌همراه همه زیرپروژه‌های داخلش؛ به‌صورت لحظه‌ای ساخته می‌شود", {
        "project_id": {"type": "integer"},
    }, ["project_id"]),
    _function("get_program_json_template",
        "بازگشت قالب JSON کامل و پویا برای یک طرح به‌همراه همه پروژه‌ها و زیرپروژه‌های داخلش در یک پاسخ؛ به‌صورت لحظه‌ای ساخته می‌شود و جایی ذخیره نمی‌شود", {
        "program_id": {"type": "integer"},
    }, ["program_id"]),
    _function("validate_project", "کنترل صحت تعریف پروژه و زیرپروژه‌های آن", {
        "project_id": {"type": "integer"},
    }, ["project_id"]),
    _function("financial_audit", "ممیزی قطعی تخصیص، قرارداد، سند و پرداخت پروژه", {
        "project_id": {"type": "integer"},
    }, ["project_id"]),
    _function("project_forecast", "محاسبه قطعی و توضیح‌پذیر SPI، CPI و تاریخ احتمالی پایان زیرپروژه‌های یک پروژه", {
        "project_id": {"type": "integer"},
    }, ["project_id"]),
    _function("explain_field", "توضیح کاربرد یک فیلد سامانه", {
        "entity": {"type": "string", "enum": ["program", "project", "subproject"]},
        "field": {"type": "string"},
    }, ["entity", "field"]),
    _function("program_search", "جستجوی عوامل طرح (برنامه) با فیلترهای گزارش‌گیر (همان /reporter/program-search/). مقادیر فیلترها فقط باید از گزینه‌های مجازِ فهرست‌شده استفاده شود؛ اگر برنامه گزینه‌ای خارج از این فهرست داشت، نزدیک‌ترین گزینه مجاز انتخاب می‌شود.", {
        "query": {"type": "string"},
        "program_types": {"type": "array", "items": {"type": "string", "enum": list(_PROGRAM_TYPES)}},
        "provinces": {"type": "array", "items": {"type": "string", "enum": list(_PROVINCES)}},
        "license_states": {"type": "array", "items": {"type": "string", "enum": list(_LICENSE_STATES)}},
        "license_codes": {"type": "array", "items": {"type": "string"}},
        "from_date": {"type": "string"},
        "to_date": {"type": "string"},
        "limit": {"type": "integer", "minimum": 1, "maximum": 50},
    }),
    _function("project_search", "جستجوی عوامل پروژه با فیلترهای گزارش‌گیر (همان /reporter/search-history/ با نوع پروژه). مقادیر فیلترها فقط باید از گزینه‌های مجازِ فهرست‌شده باشد.", {
        "query": {"type": "string"},
        "project_types": {"type": "array", "items": {"type": "string", "enum": list(_PROJECT_TYPES)}},
        "project_statuses": {"type": "array", "items": {"type": "string", "enum": list(_PROJECT_STATUSES)}},
        "provinces": {"type": "array", "items": {"type": "string", "enum": list(_PROVINCES)}},
        "program_types": {"type": "array", "items": {"type": "string", "enum": list(_PROGRAM_TYPES)}},
        "license_states": {"type": "array", "items": {"type": "string", "enum": list(_LICENSE_STATES)}},
        "min_physical_progress": {"type": "number"},
        "max_physical_progress": {"type": "number"},
        "min_financial_progress": {"type": "number"},
        "max_financial_progress": {"type": "number"},
        "limit": {"type": "integer", "minimum": 1, "maximum": 50},
    }),
    _function("subproject_search", "جستجوی عوامل زیرپروژه با فیلترهای نام، مرحله، وضعیت، نوع قرارداد و پیشرفت. مقادیر فیلترها فقط باید از گزینه‌های مجازِ فهرست‌شده باشد.", {
        "query": {"type": "string"},
        "provinces": {"type": "array", "items": {"type": "string", "enum": list(_PROVINCES)}},
        "stages": {"type": "array", "items": {"type": "string", "enum": list(_SUBPROJECT_STAGES)}},
        "states": {"type": "array", "items": {"type": "string", "enum": list(_SUBPROJECT_STATES)}},
        "contract_types": {"type": "array", "items": {"type": "string", "enum": list(_CONTRACT_TYPES)}},
        "min_progress": {"type": "number"},
        "max_progress": {"type": "number"},
        "limit": {"type": "integer", "minimum": 1, "maximum": 50},
    }),
    _function("analyze_program_buildings",
        "در سطح پیشرفته: همه طرح‌های یک یا چند استان را پیمایش می‌کند، وارد همه پروژه‌های ساختمانی (نوع احداث/تکمیل) آن‌ها می‌شود و با بررسی زیرپروژه‌ها مشخص می‌کند کدام ساختمان‌ها نیمه‌کاره‌اند (پیشرفت فیزیکی کمتر از ۱۰۰٪ یا دارای زیرپروژهٔ تحویل‌نشده/در حال اجرا). برای پرسش‌های «کدام ساختمان/طرح در استان … نیمه‌کاره یا ناتمام است» از همین ابزار استفاده کن. وقتی به بیش از یک استان نیاز باشد، همه آن‌ها را در «provinces» در یک فراخوانی بده؛ برای «آذربایجان» یا «خراسان» بدون صفت، هر دو استان متناظر به‌صورت خودکار پوشش داده می‌شود.", {
        "provinces": {"type": "array", "items": {"type": "string", "enum": list(_PROVINCES)},
                      "description": "فهرست استان‌ها؛ می‌توان از «آذربایجان شرقی» و «آذربایجان غربی» و «البرز» در یک فراخوانی استفاده کرد", "minItems": 1},
        "province": {"type": "string", "enum": list(_PROVINCES),
                     "description": "برای سازگاری: یک استان (به‌جای provinces)"},
    }, []),
    _function("search_history", "فهرست تاریخچه جستجوهای گزارش‌گیر خود کاربر جاری", {
        "search_type": {"type": "string", "enum": ["", "all", "project", "subproject"]},
        "limit": {"type": "integer", "minimum": 1, "maximum": 50},
    }),
]

WEB_TOOL_SCHEMA = _function(
    "web_search",
    "جستجوی اینترنت با نتیجه، امتیاز، تاریخ و دامنه منبع؛ پاسخ باید با ارجاع به URL و تاریخ منبع ارائه شود",
    {
        "query": {"type": "string"},
        "limit": {"type": "integer", "minimum": 1, "maximum": 8},
        "domains": {"type": "array", "items": {"type": "string"}, "maxItems": 10},
        "days": {"type": "integer", "minimum": 1, "maximum": 3650},
    },
    ["query"],
)

LOCAL_JS_TOOL_SCHEMA = _function(
    "run_local_js",
    "اجرای یک فایل JavaScript محلی از پوشه مجاز سامانه؛ فقط برای اسکریپت‌های از پیش موجود و غیرتغییردهنده",
    {
        "file_path": {"type": "string", "description": "مسیر نسبی فایل .js در پوشه مجاز"},
        "arguments": {"type": "array", "items": {"type": "string"}, "maxItems": 20},
    },
    ["file_path"],
)

TODO_TOOL_SCHEMA = _function(
    "task_todo",
    "اعلام پیشرفت برنامه-کارهای (todo) خود به‌صورت شفاف در رابط کاربر؛ این ابزار چیزی در دیتابیس تغییر نمی‌دهد و فقط وضعیت هر مرحله را به کاربر نشان می‌دهد. قبل از اجرا برنامه را اعلام کن (status=created)، هنگام شروع هر مرحله in_progress و پس از اتمام completed، و در صورت شکست failed بفرست.",
    {
        "todo_id": {"type": "integer"},
        "label": {"type": "string", "description": "عنوان کوتاه فارسی این گام"},
        "status": {"type": "string", "enum": ["created", "in_progress", "completed", "failed"]},
    },
    ["todo_id", "label", "status"],
)

PLAN_SYSTEM = (
    "تو یک عامل هوشمند برنامه‌ریز هستی. درخواست کاربر را به چند گام کوتاه، دقیق و قابل‌اجرا "
    "تقسیم کن و فقط یک آرایه JSON از اشیا با کلیدهای id و task برگردان (بدون هیچ متن دیگری):\n"
    "{\"todos\": [{\"id\": 1, \"task\": \"...\"}, ...]}\n"
    "هر task باید فارسی و کوتاه باشد و مستقیماً به سویِ پاسخ به درخواست کاربر باشد."
)


def _parse_plan(content):
    """Defensively extract a [{id, task}] plan from the model's reply."""
    text = str(content or "").strip()
    if not text:
        return []
    if "{" in text:
        start = text.find("{")
        block = text[start:]
        try:
            data = json.loads(block)
        except (TypeError, ValueError):
            data = None
        if isinstance(data, dict) and isinstance(data.get("todos"), list):
            return data["todos"]
        if isinstance(data, dict) and data:
            return [{"id": k, "task": v} for k, v in data.items()
                    if isinstance(v, str) and v.strip()]
    try:
        data = json.loads(text)
    except (TypeError, ValueError):
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("todos"), list):
        return data["todos"]
    return []


_PLACEHOLDER_MARKERS = (
    "در حال بررسی", "درحال بررسی", "بررسی اطلاعات", "بررسی سامانه",
    "در حال خواندن", "در حال جستجو", "در حال بارگذاری", "در حال آماده",
    "لطفاً صبر", "لطفا صبر", "لحظه‌ای صبر", "منتظر بمان", "صبر کنید",
    "در حال پردازش", "در حال تحلیل", "در حال جمع‌آوری", "در حال ارسال",
    "لطفا منتظر", "لطفاً منتظر", "بررسی می‌شود", "در حال بررسی اطلاعات",
    "checking", "loading", "please wait", "one moment",
)


def _looks_like_placeholder(content):
    """True when the model's non-tool text is only a transitional phrase, not a
    real answer (e.g. «در حال بررسی اطلاعات سامانه…»)."""
    text = str(content or "").strip()
    if not text:
        return True
    lowered = "".join(text.split()).lower()
    return any("".join(marker.split()).lower() in lowered
               for marker in _PLACEHOLDER_MARKERS)


def _placeholder_fallback(current):
    """Synthesize a concrete fallback answer from the tool results actually
    gathered during the loop, since the model refused to write one."""
    facts = []
    for msg in current or []:
        if msg.get("role") != "tool":
            continue
        raw = msg.get("content")
        try:
            data = json.loads(raw) if isinstance(raw, str) else raw
        except (TypeError, ValueError):
            continue
        if isinstance(data, dict):
            if "result" in data and data["result"]:
                facts.append(str(data["result"]))
            elif "count" in data:
                facts.append(f"{data.get('count')} مورد")
    if facts:
        return ("بر اساس داده‌هایی که از سامانه بازیابی شد این خلاصه در دسترس است: "
                + "؛ ".join(dict.fromkeys(facts))[:1200])
    return ("برای پاسخ به این پرسش، داده‌ای از ابزارهای سامانه بازیابی نشد؛ "
            "لطفاً درخواست را دوباره یا با جزئیات بیشتر مطرح کنید.")


def _execute_tool(user, name, args, allow_web_search, allow_local_js,
                  progress=None):
    if name == "task_todo":
        # A live-UI signal only; never touches the database.
        status = args.get("status", "created")
        label = str(args.get("label", "")).strip()
        todo_id = args.get("todo_id")
        if progress:
            try:
                progress({"kind": "todo", "todo_id": todo_id, "label": label,
                          "status": status})
            except Exception:
                pass
        return {"ok": True, "todo_id": todo_id, "todo": label, "status": status}
    if name == "system_overview":
        return system_overview(user)
    if name == "search_site":
        return search_site(user, args["query"], args.get("entity", "all"), args.get("limit", 10))
    if name == "read_program":
        return read_program(user, args["program_id"])
    if name == "read_project":
        return read_project(user, args["project_id"])
    if name == "read_subproject":
        return read_subproject(user, args["subproject_id"])
    if name == "get_subproject_json_template":
        return get_subproject_json_template(user, args["subproject_id"])
    if name == "get_project_json_template":
        return get_project_json_template(user, args["project_id"])
    if name == "get_program_json_template":
        return get_program_json_template(user, args["program_id"])
    if name == "validate_project":
        return validate_project(user, args["project_id"])
    if name == "financial_audit":
        return financial_audit(user, args["project_id"])
    if name == "project_forecast":
        return project_forecast(user, args["project_id"])
    if name == "explain_field":
        return explain_field(args["entity"], args["field"]) or {"error": "فیلد پیدا نشد."}
    if name == "program_search":
        return search_programs(
            user, query=args.get("query", ""),
            program_types=args.get("program_types"),
            provinces=args.get("provinces"),
            license_states=args.get("license_states"),
            license_codes=args.get("license_codes"),
            from_date=args.get("from_date", ""),
            to_date=args.get("to_date", ""),
            limit=args.get("limit", 20))
    if name == "project_search":
        return search_projects(
            user, query=args.get("query", ""),
            project_types=args.get("project_types"),
            project_statuses=args.get("project_statuses"),
            provinces=args.get("provinces"),
            program_types=args.get("program_types"),
            license_states=args.get("license_states"),
            min_physical_progress=args.get("min_physical_progress"),
            max_physical_progress=args.get("max_physical_progress"),
            min_financial_progress=args.get("min_financial_progress"),
            max_financial_progress=args.get("max_financial_progress"),
            limit=args.get("limit", 20))
    if name == "subproject_search":
        return search_subprojects(
            user, query=args.get("query", ""),
            provinces=args.get("provinces"), stages=args.get("stages"),
            states=args.get("states"), contract_types=args.get("contract_types"),
            min_progress=args.get("min_progress"),
            max_progress=args.get("max_progress"),
            limit=args.get("limit", 20))
    if name == "search_history":
        return search_history(user, search_type=args.get("search_type", ""),
                              limit=args.get("limit", 20))
    if name == "analyze_program_buildings":
        return analyze_program_buildings(
            user, province=args.get("province"), provinces=args.get("provinces"))
    if name == "web_search":
        if not allow_web_search:
            raise PermissionError("جستجوی وب برای این حساب یا این درخواست فعال نیست.")
        return tavily_search(
            args["query"], limit=args.get("limit", 5),
            domains=args.get("domains"), days=args.get("days"), user=user,
        )
    if name == "run_local_js":
        if not allow_local_js:
            raise PermissionError("اجرای JavaScript محلی برای این حساب یا سرور فعال نیست.")
        return run_local_js(args["file_path"], args.get("arguments", []))
    raise ValueError("ابزار ناشناخته است.")


def _tool_name_fa(name):
    """Short Persian label for a tool used inside the live feed."""
    return {
        "system_overview": "نمای کلی سیستم",
        "search_site": "جستجوی سامانه",
        "read_program": "خواندن طرح",
        "read_project": "خواندن پروژه",
        "read_subproject": "خواندن زیرپروژه",
        "get_program_json_template": "قالب JSON طرح",
        "get_project_json_template": "قالب JSON پروژه",
        "get_subproject_json_template": "قالب JSON زیرپروژه",
        "validate_project": "اعتبارسنجی پروژه",
        "financial_audit": "ممیزی مالی",
        "project_forecast": "پیش‌بینی/SPI-CPI",
        "explain_field": "راهنمای فیلد",
        "program_search": "جستجوی طرح",
        "project_search": "جستجوی پروژه",
        "subproject_search": "جستجوی زیرپروژه",
        "search_history": "تاریخچه جستجو",
        "analyze_program_buildings": "تحلیل ساختمان‌های نیمه‌کاره",
        "web_search": "جستجوی وب",
        "run_local_js": "اجرای اسکریپت",
        "task_todo": "گام برنامه",
    }.get(name, name)


def _record_label(model, qs_name, object_id):
    """Resolve a short title for a record id within the visible scope; safe."""
    if not object_id:
        return None
    try:
        row = qs_name(_RECORD_USER).filter(pk=int(object_id)).first()
        if row is None:
            return str(object_id)
        if model is Program:
            title = getattr(row, "title", "") or ""
            return f"{title} [{getattr(row, 'program_id', '')}]" if title else str(object_id)
        if model is Project:
            title = getattr(row, "name", "") or ""
            return f"{title} [{getattr(row, 'project_id', '')}]" if title else str(object_id)
        if model is SubProject:
            return (getattr(row, "name", "") or getattr(row, "project_stage", "") or str(object_id))
    except Exception:
        return str(object_id)
    return str(object_id)


_RECORD_USER = None


def _list_filters(args):
    """Comma-joined, non-empty filter values for a search description."""
    parts = []
    for key, label in (("provinces", "استان"), ("program_types", "نوع طرح"),
                       ("project_types", "نوع پروژه"), ("stages", "مرحله"),
                       ("states", "وضعیت"), ("contract_types", "قرارداد")):
        value = args.get(key)
        if value:
            parts.append(f"{label}: {', '.join(str(v) for v in value if str(v).strip())}")
    return "، ".join(parts)


def _describe_tool(name, args, user=None):
    """Concrete, Cursor-style Persian description of the next tool action,
    including the actual records (titles/ids), provinces and queries."""
    global _RECORD_USER
    if user is not None:
        _RECORD_USER = user
    args = args or {}
    if name == "task_todo":
        return f"گام: {str(args.get('label', '')).strip() or '…'}"

    if name == "system_overview":
        return "نمای کلی از تعداد طرح/پروژه/زیرپروژهٔ قابل مشاهده و تخصیص مالی"
    if name == "search_site":
        return f"جستجوی «{args.get('query', '')}» در {args.get('entity', 'سامانه')}"
    if name == "read_program":
        return f"خواندن جزئیات طرح {_record_label(Program, visible_programs, args.get('program_id'))}"
    if name == "read_project":
        return f"خواندن جزئیات پروژه {_record_label(Project, visible_projects, args.get('project_id'))}"
    if name == "read_subproject":
        return f"خواندن جزئیات زیرپروژه {_record_label(SubProject, visible_subprojects, args.get('subproject_id'))}"
    if name == "get_program_json_template":
        return f"ساخت قالب JSON کامل طرح {_record_label(Program, visible_programs, args.get('program_id'))}"
    if name == "get_project_json_template":
        return f"ساخت قالب JSON کامل پروژه {_record_label(Project, visible_projects, args.get('project_id'))}"
    if name == "get_subproject_json_template":
        return f"ساخت قالب JSON کامل زیرپروژه {_record_label(SubProject, visible_subprojects, args.get('subproject_id'))}"
    if name == "validate_project":
        return f"اعتبارسنجی تعریف پروژه {_record_label(Project, visible_projects, args.get('project_id'))}"
    if name == "financial_audit":
        return f"ممیزی تخصیص/قرارداد/سند/پرداخت پروژه {_record_label(Project, visible_projects, args.get('project_id'))}"
    if name == "project_forecast":
        return f"محاسبه SPI/CPI و تاریخ پایان پروژه {_record_label(Project, visible_projects, args.get('project_id'))}"
    if name == "explain_field":
        return f"توضیح کاربرد فیلد «{args.get('field', '')}» در {args.get('entity', '')}"
    if name == "program_search":
        return "جستجوی طرح‌ها" + (f" در استان {', '.join(args.get('provinces', []))}"
                                  if args.get("provinces") else "") + \
               (f" (نوع: {', '.join(args.get('program_types', []))})" if args.get("program_types") else "")
    if name == "project_search":
        return "جستجوی پروژه‌ها" + (f" در استان {', '.join(args.get('provinces', []))}"
                                    if args.get("provinces") else "") + \
               (f" (نوع: {', '.join(args.get('project_types', []))})" if args.get("project_types") else "")
    if name == "subproject_search":
        return "جستجوی زیرپروژه‌ها" + (f" در استان {', '.join(args.get('provinces', []))}"
                                       if args.get("provinces") else "") + \
               (f" (مرحله: {', '.join(args.get('stages', []))})" if args.get("stages") else "")
    if name == "search_history":
        return f"خواندن تاریخچه جستجوهای شما (نوع: {args.get('search_type', '') or 'همه'})"
    if name == "analyze_program_buildings":
        provs = args.get("provinces") or ([args.get("province")] if args.get("province") else [])
        prov_text = "، ".join(provs) if provs else "استان(های) خواسته‌شده"
        return (f"پیمایش عمیق ساختمان‌های نیمه‌کاره در {prov_text}: "
                f"همه طرح‌ها ← پروژه‌های احداث/تکمیل ← زیرپروژه‌ها")
    if name == "web_search":
        return f"جستجوی اینترنت برای «{args.get('query', '')}»"
    if name == "run_local_js":
        return f"اجرای اسکریپت محلی «{args.get('file_path', '')}»"
    return "در حال پردازش…"


def _emit(progress, event):
    if progress:
        try:
            progress(event)
        except Exception:
            pass


def run_agentic_loop(user, messages, provider, allow_web_search=False,
                     allow_local_js=False, max_rounds=3, progress=None):
    """Agentic loop with a visible plan + todo checklist (Cursor-like).

    1. Asks the model for a short todo plan and streams it as `plan` events.
    2. Runs the bounded tool loop, streaming a `step` ("what tool / doing what")
       event per executed tool and forwarding optional `task_todo` signals.
    3. Returns the final Persian answer plus the collected trace.

    progress events: 
      {"kind":"plan","status":"created","todos":[{id,task},...]}
      {"kind":"todo","todo_id":..,"label":..,"status":"created|in_progress|completed|failed"}
      {"kind":"step","step":..,"tool":..,"text":..,"state":"running|done|error"}
      {"kind":"plan","status":"done"}
    """
    schemas = list(BASE_TOOL_SCHEMAS)
    schemas.append(TODO_TOOL_SCHEMA)
    if allow_web_search:
        schemas.append(WEB_TOOL_SCHEMA)
    if allow_local_js and os.getenv("AI_LOCAL_JS_ENABLED", "false").lower() in {"1", "true", "yes"}:
        schemas.append(LOCAL_JS_TOOL_SCHEMA)

    plan = []
    try:
        plan_result = provider.complete(
            [{"role": "system", "content": PLAN_SYSTEM},
             {"role": "user", "content": str(messages[-1].get("content", ""))}],
            tools=None, user=user)
        plan = _parse_plan(plan_result.get("content", ""))
    except Exception:
        plan = []
    plan = plan[:10]

    current = list(messages)
    trace = []
    step = 0

    if plan:
        _emit(progress, {"kind": "plan", "status": "created", "todos": [
            {"id": t.get("id", i + 1), "task": str(t.get("task", "")).strip()}
            for i, t in enumerate(plan)]})
    else:
        _emit(progress, {"kind": "plan", "status": "created", "todos": []})
    _emit(progress, {"kind": "step", "step": 0, "tool": "",
                     "text": "تحلیل درخواست و برنامه‌ریزی…", "state": "thinking"})

    for _round in range(max_rounds):
        result = provider.complete(current, tools=schemas, user=user)
        assistant_message = result["message"] or {"role": "assistant", "content": result["content"]}
        calls = assistant_message.get("tool_calls") or []
        if not calls:
            content = str(result.get("content") or "")
            if _looks_like_placeholder(content):
                # The model only typed a transitional phrase (like
                # «در حال بررسی اطلاعات سامانه…») without a real answer. We do
                # NOT surface that generic line in the feed (it would look like
                # noise); instead we force a real answer from the data gathered
                # so far and hand it to the UI as the final answer.
                final_result = provider.complete(
                    current + [{"role": "assistant", "content": content},
                               {"role": "user",
                                "content": "پاسخ نهایی کامل و قابل استفاده خود را طبق "
                                           "اطلاعاتی که تاکنون از ابزارها به دست آورده‌ای "
                                           "بساز و ارائه کن (بدون جمله‌های انتظار/بررسی)."}],
                    tools=[], user=user)
                content = str(final_result.get("content") or "")
                usage = final_result.get("usage", {})
                if _looks_like_placeholder(content):
                    final_result = provider.complete(
                        current + [{"role": "assistant", "content": content},
                                   {"role": "user",
                                    "content": "پاسخ قطعی و کامل خود را همین حالا بنویس؛ "
                                               "از هرگونه عبارت انتظار مانند «در حال بررسی» "
                                               "خودداری کن و مستقیم به پرسش کاربر پاسخ بده."}],
                        tools=[], user=user)
                    content = str(final_result.get("content") or "")
                    usage = final_result.get("usage", {})
                    if _looks_like_placeholder(content):
                        content = _placeholder_fallback(current)
                if plan:
                    for t in plan:
                        _emit(progress, {"kind": "todo",
                                         "todo_id": t.get("id", ""),
                                         "label": str(t.get("task", "")).strip(),
                                         "status": "completed"})
                _emit(progress, {"kind": "plan", "status": "done"})
                return {"content": content, "trace": trace,
                        "plan": plan, "usage": usage}
            if plan:
                for t in plan:
                    _emit(progress, {"kind": "todo",
                                     "todo_id": t.get("id", ""),
                                     "label": str(t.get("task", "")).strip(),
                                     "status": "completed"})
            _emit(progress, {"kind": "plan", "status": "done"})
            return {"content": content, "trace": trace,
                    "plan": plan, "usage": result.get("usage", {})}
        current.append(assistant_message)
        for index, call in enumerate(calls):
            function = call.get("function") or {}
            name = function.get("name", "")
            args = {}
            try:
                args = json.loads(function.get("arguments") or "{}")
            except (TypeError, ValueError):
                args = {}
            step += 1
            defaulted = index >= 6
            tool_fa = _tool_name_fa(name)
            desc = _describe_tool(name, args, user)
            if defaulted:
                value = {"error": "تعداد ابزارهای این مرحله از سقف مجاز بیشتر است."}
                trace.append({"tool": name, "ok": False, "error": "tool_limit"})
                _emit(progress, {"kind": "step", "step": step, "tool": name,
                                 "tool_fa": tool_fa, "text": desc,
                                 "state": "error", "error": "tool_limit"})
            else:
                _emit(progress, {"kind": "step", "step": step, "tool": name,
                                 "tool_fa": tool_fa, "text": desc, "state": "running"})
                try:
                    value = _execute_tool(user, name, args, allow_web_search,
                                          allow_local_js, progress=progress)
                    trace.append({"tool": name, "ok": True})
                    _emit(progress, {"kind": "step", "step": step, "tool": name,
                                     "state": "done"})
                except Exception as exc:
                    value = {"error": str(exc)}
                    trace.append({"tool": name, "ok": False, "error": type(exc).__name__})
                    _emit(progress, {"kind": "step", "step": step, "tool": name,
                                     "state": "error", "error": type(exc).__name__})
            current.append({
                "role": "tool", "tool_call_id": call.get("id", ""),
                "name": name, "content": json.dumps(value, ensure_ascii=False, default=str),
            })

    trace.append({"tool": "final_response", "ok": True, "error": "tool_round_limit"})
    final_result = provider.complete(current, tools=[], user=user)
    content = final_result.get("content") or "اطلاعات لازم دریافت شد، اما تولید پاسخ نهایی کامل نشد."
    if plan:
        for t in plan:
            _emit(progress, {"kind": "todo", "todo_id": t.get("id", ""),
                             "label": str(t.get("task", "")).strip(),
                             "status": "completed"})
    _emit(progress, {"kind": "plan", "status": "done"})
    return {
        "content": content,
        "trace": trace,
        "plan": plan,
        "usage": final_result.get("usage", {}),
    }


def run_tool_loop(user, messages, provider, allow_web_search=False,
                  allow_local_js=False, max_rounds=3, progress=None):
    """Backward-compatible alias: an agentic loop without the visible plan."""
    return run_agentic_loop(user, messages, provider,
                            allow_web_search=allow_web_search,
                            allow_local_js=allow_local_js,
                            max_rounds=max_rounds, progress=progress)
