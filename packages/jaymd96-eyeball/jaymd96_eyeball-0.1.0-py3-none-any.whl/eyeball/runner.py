"""Code execution utilities for eyeball."""

from __future__ import annotations

import asyncio
import contextlib
import inspect
import io
import traceback
from typing import Any

from eyeball.resolver import ResolvedTarget


def run_target(resolved: ResolvedTarget, args: list[Any] | None = None, kwargs: dict[str, Any] | None = None) -> dict[str, Any]:
    """Execute a resolved target (function/method) with arguments."""
    if resolved.error:
        return {"status": "error", "target": resolved.original, "error": resolved.error}

    if resolved.target_type not in ("function", "class"):
        return {"status": "error", "target": resolved.original, "error": f"Cannot run target of type '{resolved.target_type}'. Use exec for arbitrary code."}

    args = args or []
    kwargs = kwargs or {}
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    result = error = tb = None

    try:
        with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
            target = resolved.symbol
            if asyncio.iscoroutinefunction(target):
                result = asyncio.run(target(*args, **kwargs))
            else:
                result = target(*args, **kwargs)
    except Exception as e:
        error = str(e)
        tb = traceback.format_exc()

    stdout = stdout_capture.getvalue()
    stderr = stderr_capture.getvalue()

    if error:
        return {"status": "error", "target": resolved.original, "error": error, "traceback": tb, "stdout": stdout or None, "stderr": stderr or None}

    return {"status": "success", "target": resolved.original, "result": _serialize_result(result), "result_type": type(result).__name__, "stdout": stdout or None, "stderr": stderr or None}


def exec_code(code: str, namespace: dict[str, Any] | None = None) -> dict[str, Any]:
    """Execute arbitrary Python code."""
    if namespace is None:
        namespace = {}
    namespace.setdefault("__builtins__", __builtins__)

    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    error = tb = result = None
    original_keys = set(namespace.keys())

    try:
        with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
            try:
                result = eval(code, namespace)
            except SyntaxError:
                exec(code, namespace)
                result = None
    except Exception as e:
        error = str(e)
        tb = traceback.format_exc()

    stdout = stdout_capture.getvalue()
    stderr = stderr_capture.getvalue()
    new_keys = set(namespace.keys()) - original_keys - {"__builtins__"}
    new_vars = {key: _serialize_result(namespace[key]) for key in new_keys}

    if error:
        return {"status": "error", "error": error, "traceback": tb, "stdout": stdout or None, "stderr": stderr or None}

    return {"status": "success", "result": _serialize_result(result) if result is not None else None, "result_type": type(result).__name__ if result is not None else None, "new_variables": new_vars or None, "stdout": stdout or None, "stderr": stderr or None}


def _serialize_result(obj: Any, max_depth: int = 3) -> Any:
    """Serialize a result for JSON output."""
    if obj is None:
        return None
    if isinstance(obj, (bool, int, float, str)):
        return obj
    if isinstance(obj, bytes):
        try:
            return obj.decode("utf-8")
        except UnicodeDecodeError:
            return f"<bytes: {len(obj)} bytes>"
    if isinstance(obj, (list, tuple)):
        if max_depth <= 0:
            return f"<{type(obj).__name__}: {len(obj)} items>"
        return [_serialize_result(item, max_depth - 1) for item in obj[:100]]
    if isinstance(obj, dict):
        if max_depth <= 0:
            return f"<dict: {len(obj)} items>"
        return {str(k): _serialize_result(v, max_depth - 1) for k, v in list(obj.items())[:100]}
    if isinstance(obj, set):
        if max_depth <= 0:
            return f"<set: {len(obj)} items>"
        return list(obj)[:100]
    if hasattr(obj, "model_dump"):
        try:
            return obj.model_dump()
        except Exception:
            pass
    if hasattr(obj, "__dataclass_fields__"):
        try:
            from dataclasses import asdict
            return asdict(obj)
        except Exception:
            pass
    if hasattr(obj, "__table__"):
        try:
            return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
        except Exception:
            pass
    if hasattr(obj, "__dict__"):
        if max_depth <= 0:
            return f"<{type(obj).__name__}>"
        return {"__type__": type(obj).__name__, **{k: _serialize_result(v, max_depth - 1) for k, v in obj.__dict__.items() if not k.startswith("_")}}
    try:
        r = repr(obj)
        return r[:197] + "..." if len(r) > 200 else r
    except Exception:
        return f"<{type(obj).__name__}>"


def get_source(resolved: ResolvedTarget) -> dict[str, Any]:
    """Get source code for a resolved target."""
    if resolved.error:
        return {"status": "error", "target": resolved.original, "error": resolved.error}

    target = resolved.symbol if resolved.symbol else resolved.module

    try:
        source = inspect.getsource(target)
        lines, start_line = inspect.getsourcelines(target)
        file_path = inspect.getfile(target)
        return {"status": "success", "target": resolved.original, "file_path": file_path, "start_line": start_line, "end_line": start_line + len(lines) - 1, "source": source}
    except (TypeError, OSError) as e:
        return {"status": "error", "target": resolved.original, "error": f"Cannot get source: {e}"}
