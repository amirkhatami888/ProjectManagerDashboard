"""Safe, explicitly configured local JavaScript runner.

This is intentionally a file runner, not a shell tool.  Files must live under
AI_JS_WORKSPACE_ROOT and Node is invoked with an argv list (shell=False).
"""
import os
import shutil
import subprocess
from pathlib import Path

from django.conf import settings


class JavaScriptRunnerError(RuntimeError):
    pass


def _workspace_root():
    configured = os.getenv("AI_JS_WORKSPACE_ROOT", "").strip()
    return Path(configured or (Path(settings.BASE_DIR) / "ai_scripts")).resolve()


def run_local_js(file_path, arguments=None, timeout_seconds=None):
    if os.getenv("AI_LOCAL_JS_ENABLED", "false").lower() not in {"1", "true", "yes"}:
        raise PermissionError("اجرای فایل JavaScript محلی فعال نشده است.")
    node = os.getenv("AI_NODE_BINARY", "node").strip() or "node"
    node_path = shutil.which(node) or (node if Path(node).is_file() else None)
    if not node_path:
        raise JavaScriptRunnerError("Node.js روی سرور پیدا نشد.")

    root = _workspace_root()
    candidate = Path(str(file_path or "").strip())
    if candidate.is_absolute():
        raise PermissionError("مسیر فایل باید نسبی به پوشه JavaScript مجاز باشد.")
    if candidate.suffix.lower() != ".js":
        raise ValueError("فقط فایل‌های .js قابل اجرا هستند.")
    resolved = (root / candidate).resolve()
    if root != resolved and root not in resolved.parents:
        raise PermissionError("فایل خارج از پوشه JavaScript مجاز است.")
    if not resolved.is_file():
        raise FileNotFoundError("فایل JavaScript پیدا نشد.")

    args = arguments or []
    if not isinstance(args, list) or len(args) > 20 or any(not isinstance(x, str) for x in args):
        raise ValueError("arguments باید فهرستی از حداکثر ۲۰ رشته باشد.")
    timeout = max(1, min(int(timeout_seconds or os.getenv("AI_JS_TIMEOUT_SECONDS", "20")), 60))
    try:
        completed = subprocess.run(
            [node_path, "--no-warnings", str(resolved), *args],
            cwd=str(root), capture_output=True, text=True, timeout=timeout,
            check=False, shell=False,
            env={"PATH": os.getenv("PATH", ""), "NODE_ENV": "production"},
        )
    except subprocess.TimeoutExpired as exc:
        raise JavaScriptRunnerError(f"اجرای JavaScript پس از {timeout} ثانیه متوقف شد.") from exc
    return {
        "file": str(candidate),
        "exit_code": completed.returncode,
        "stdout": completed.stdout[-12000:],
        "stderr": completed.stderr[-12000:],
        "ok": completed.returncode == 0,
    }
