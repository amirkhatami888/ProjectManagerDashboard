"""Bounded agent loop with explicit, permission-aware Django tools."""
import json

from .domain_tools import (
    financial_audit, read_program, read_project, read_subproject, search_site,
    project_forecast, system_overview, validate_project,
)
from .search import tavily_search
from .tools import explain_field
from .js_runner import run_local_js
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


def _execute_tool(user, name, args, allow_web_search, allow_local_js):
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
    if name == "validate_project":
        return validate_project(user, args["project_id"])
    if name == "financial_audit":
        return financial_audit(user, args["project_id"])
    if name == "project_forecast":
        return project_forecast(user, args["project_id"])
    if name == "explain_field":
        return explain_field(args["entity"], args["field"]) or {"error": "فیلد پیدا نشد."}
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


def run_tool_loop(user, messages, provider, allow_web_search=False,
                  allow_local_js=False, max_rounds=5):
    """Return final text and a safe trace; authorization is repeated per tool."""
    current = list(messages)
    schemas = list(BASE_TOOL_SCHEMAS)
    if allow_web_search:
        schemas.append(WEB_TOOL_SCHEMA)
    if allow_local_js and os.getenv("AI_LOCAL_JS_ENABLED", "false").lower() in {"1", "true", "yes"}:
        schemas.append(LOCAL_JS_TOOL_SCHEMA)
    trace = []
    for _round in range(max_rounds):
        result = provider.complete(current, tools=schemas, user=user)
        assistant_message = result["message"] or {"role": "assistant", "content": result["content"]}
        calls = assistant_message.get("tool_calls") or []
        if not calls:
            return {"content": result["content"], "trace": trace, "usage": result.get("usage", {})}
        current.append(assistant_message)
        for index, call in enumerate(calls):
            function = call.get("function") or {}
            name = function.get("name", "")
            if index >= 6:
                # Every tool_call_id must receive a tool message, even when
                # the safety limit prevents executing that call.
                value = {"error": "تعداد ابزارهای این مرحله از سقف مجاز بیشتر است."}
                trace.append({"tool": name, "ok": False, "error": "tool_limit"})
            else:
                try:
                    args = json.loads(function.get("arguments") or "{}")
                    value = _execute_tool(user, name, args, allow_web_search, allow_local_js)
                    trace.append({"tool": name, "ok": True})
                except Exception as exc:
                    value = {"error": str(exc)}
                    trace.append({"tool": name, "ok": False, "error": type(exc).__name__})
            current.append({
                "role": "tool", "tool_call_id": call.get("id", ""),
                "name": name, "content": json.dumps(value, ensure_ascii=False, default=str),
            })
    # The model may keep asking for tools even after all requested data has
    # been collected. Make one final tool-free call so this becomes a usable
    # answer instead of an Internal Server Error.
    trace.append({"tool": "final_response", "ok": True, "error": "tool_round_limit"})
    final_result = provider.complete(current, tools=[], user=user)
    content = final_result.get("content") or "اطلاعات لازم دریافت شد، اما تولید پاسخ نهایی کامل نشد."
    return {
        "content": content,
        "trace": trace,
        "usage": final_result.get("usage", {}),
    }
