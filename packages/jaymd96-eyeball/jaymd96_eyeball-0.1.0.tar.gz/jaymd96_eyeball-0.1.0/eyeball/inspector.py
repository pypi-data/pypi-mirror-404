"""Inspection utilities for eyeball."""

from __future__ import annotations

import inspect
from typing import Any, get_type_hints

from eyeball.resolver import ResolvedTarget


def inspect_target(resolved: ResolvedTarget) -> dict[str, Any]:
    """Inspect a resolved target and return structured information."""
    if resolved.error:
        return {"status": "error", "target": resolved.original, "error": resolved.error}

    if resolved.target_type == "module":
        return _inspect_module(resolved)
    elif resolved.target_type == "class":
        return _inspect_class(resolved)
    elif resolved.target_type == "function":
        return _inspect_function(resolved)
    elif resolved.target_type == "attribute":
        return _inspect_attribute(resolved)
    else:
        return {"status": "error", "target": resolved.original, "error": f"Unknown target type: {resolved.target_type}"}


def _inspect_module(resolved: ResolvedTarget) -> dict[str, Any]:
    """Inspect a module."""
    module = resolved.module
    classes, functions, constants, submodules = [], [], [], []

    for name in dir(module):
        if name.startswith("_"):
            continue
        try:
            obj = getattr(module, name)
        except Exception:
            continue

        obj_module = getattr(obj, "__module__", None)

        if isinstance(obj, type):
            classes.append({"name": name, "defined_here": obj_module == resolved.module_name, "bases": [b.__name__ for b in obj.__bases__ if b is not object]})
        elif callable(obj):
            functions.append({"name": name, "defined_here": obj_module == resolved.module_name, "signature": _get_signature_str(obj)})
        elif isinstance(obj, type(module)):
            submodules.append(name)
        elif not callable(obj):
            constants.append({"name": name, "type": type(obj).__name__, "value": _safe_repr(obj)})

    return {
        "status": "success", "target": resolved.original, "type": "module",
        "module_name": resolved.module_name, "file_path": str(resolved.file_path) if resolved.file_path else None,
        "docstring": _clean_docstring(module.__doc__),
        "classes": sorted(classes, key=lambda x: (not x["defined_here"], x["name"])),
        "functions": sorted(functions, key=lambda x: (not x["defined_here"], x["name"])),
        "constants": sorted(constants, key=lambda x: x["name"]),
        "submodules": sorted(submodules),
    }


def _inspect_class(resolved: ResolvedTarget) -> dict[str, Any]:
    """Inspect a class."""
    cls = resolved.symbol
    methods, class_methods, static_methods, properties = [], [], [], []

    for name in dir(cls):
        if name.startswith("_") and not name.startswith("__"):
            continue
        if name.startswith("__") and name not in ("__init__", "__call__", "__enter__", "__exit__"):
            continue

        try:
            obj = getattr(cls, name)
        except Exception:
            continue

        defined_in = None
        for klass in cls.__mro__:
            if name in klass.__dict__:
                defined_in = klass.__name__
                break

        if isinstance(obj, property):
            properties.append({"name": name, "defined_in": defined_in, "has_setter": obj.fset is not None})
        elif isinstance(obj, classmethod) or (hasattr(obj, "__self__") and obj.__self__ is cls):
            class_methods.append({"name": name, "defined_in": defined_in, "signature": _get_signature_str(obj)})
        elif isinstance(obj, staticmethod):
            static_methods.append({"name": name, "defined_in": defined_in, "signature": _get_signature_str(obj.__func__ if hasattr(obj, "__func__") else obj)})
        elif callable(obj):
            methods.append({"name": name, "defined_in": defined_in, "signature": _get_signature_str(obj)})

    attributes = []
    annotations = getattr(cls, "__annotations__", {})
    for name, type_hint in annotations.items():
        if not name.startswith("_"):
            default = cls.__dict__.get(name, "<required>")
            attributes.append({"name": name, "type": _type_to_str(type_hint), "default": _safe_repr(default) if default != "<required>" else None, "required": default == "<required>"})

    init_signature = _get_signature_str(cls.__init__) if hasattr(cls, "__init__") else None

    return {
        "status": "success", "target": resolved.original, "type": "class",
        "class_name": cls.__name__, "module_name": resolved.module_name,
        "file_path": str(resolved.file_path) if resolved.file_path else None,
        "line_number": resolved.line_number, "docstring": _clean_docstring(cls.__doc__),
        "bases": [b.__name__ for b in cls.__bases__ if b is not object],
        "init_signature": init_signature, "attributes": attributes,
        "properties": sorted(properties, key=lambda x: x["name"]),
        "methods": sorted(methods, key=lambda x: x["name"]),
        "class_methods": sorted(class_methods, key=lambda x: x["name"]),
        "static_methods": sorted(static_methods, key=lambda x: x["name"]),
    }


def _inspect_function(resolved: ResolvedTarget) -> dict[str, Any]:
    """Inspect a function or method."""
    func = resolved.symbol
    parameters = []
    return_type = None

    try:
        sig = inspect.signature(func)
        hints = get_type_hints(func) if hasattr(func, "__annotations__") else {}

        for name, param in sig.parameters.items():
            if name == "self":
                continue
            param_info = {
                "name": name, "kind": str(param.kind).split(".")[-1],
                "type": _type_to_str(hints.get(name)), "default": None,
                "required": param.default is inspect.Parameter.empty,
            }
            if param.default is not inspect.Parameter.empty:
                param_info["default"] = _safe_repr(param.default)
            parameters.append(param_info)

        return_type = _type_to_str(hints.get("return"))
    except (ValueError, TypeError):
        pass

    return {
        "status": "success", "target": resolved.original, "type": "function",
        "function_name": func.__name__, "module_name": resolved.module_name,
        "file_path": str(resolved.file_path) if resolved.file_path else None,
        "line_number": resolved.line_number, "docstring": _clean_docstring(func.__doc__),
        "signature": _get_signature_str(func), "parameters": parameters, "return_type": return_type,
        "is_async": inspect.iscoroutinefunction(func), "is_generator": inspect.isgeneratorfunction(func),
    }


def _inspect_attribute(resolved: ResolvedTarget) -> dict[str, Any]:
    """Inspect an attribute value."""
    value = resolved.symbol
    return {
        "status": "success", "target": resolved.original, "type": "attribute",
        "value_type": type(value).__name__, "value": _safe_repr(value),
        "module_name": resolved.module_name,
        "file_path": str(resolved.file_path) if resolved.file_path else None,
    }


def _get_signature_str(obj: Any) -> str | None:
    try:
        return str(inspect.signature(obj))
    except (ValueError, TypeError):
        return None


def _type_to_str(type_hint: Any) -> str | None:
    if type_hint is None:
        return None
    if hasattr(type_hint, "__name__"):
        return type_hint.__name__
    return str(type_hint).replace("typing.", "")


def _clean_docstring(doc: str | None) -> str | None:
    if not doc:
        return None
    lines = doc.strip().split("\n")
    if not lines:
        return None
    min_indent = float("inf")
    for line in lines[1:]:
        stripped = line.lstrip()
        if stripped:
            min_indent = min(min_indent, len(line) - len(stripped))
    if min_indent == float("inf"):
        min_indent = 0
    result = [lines[0]]
    for line in lines[1:]:
        result.append(line[min_indent:] if line.strip() and len(line) > min_indent else line)
    return "\n".join(result)


def _safe_repr(obj: Any, max_length: int = 100) -> str:
    try:
        r = repr(obj)
        return r[:max_length - 3] + "..." if len(r) > max_length else r
    except Exception:
        return f"<{type(obj).__name__}>"


def discover_module(resolved: ResolvedTarget) -> dict[str, Any]:
    """Discover all public items in a module."""
    if resolved.error:
        return {"status": "error", "target": resolved.original, "error": resolved.error}
    if resolved.target_type != "module":
        return {"status": "error", "target": resolved.original, "error": f"discover only works on modules, got {resolved.target_type}"}

    module = resolved.module
    items = []

    for name in dir(module):
        if name.startswith("_"):
            continue
        try:
            obj = getattr(module, name)
        except Exception:
            continue

        obj_module = getattr(obj, "__module__", None)
        is_local = obj_module == resolved.module_name
        full_path = f"{resolved.module_name}:{name}"

        if isinstance(obj, type):
            items.append({"path": full_path, "name": name, "type": "class", "local": is_local, "docstring": _clean_docstring(obj.__doc__)})
        elif callable(obj):
            items.append({"path": full_path, "name": name, "type": "function", "local": is_local, "signature": _get_signature_str(obj)})

    items.sort(key=lambda x: (not x["local"], x["name"]))

    return {
        "status": "success", "target": resolved.original, "module_name": resolved.module_name,
        "file_path": str(resolved.file_path) if resolved.file_path else None,
        "items": items, "total": len(items), "local": sum(1 for i in items if i["local"]),
    }
