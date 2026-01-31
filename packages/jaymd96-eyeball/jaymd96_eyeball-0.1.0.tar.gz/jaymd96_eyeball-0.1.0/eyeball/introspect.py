"""Deep introspection utilities for exploring libraries and APIs.

Designed for verifying correct usage of third-party libraries by providing:
- Function/method signatures with full type hints
- Docstrings with parsed examples
- Parameter descriptions
- Source code snippets
- Related methods/classes
"""

from __future__ import annotations

import ast
import inspect
import re
from dataclasses import dataclass, field
from typing import Any, get_type_hints

from eyeball.resolver import ResolvedTarget


@dataclass
class Parameter:
    """Detailed parameter information."""
    name: str
    type_hint: str | None = None
    default: str | None = None
    required: bool = True
    kind: str = "POSITIONAL_OR_KEYWORD"  # POSITIONAL_ONLY, KEYWORD_ONLY, VAR_POSITIONAL, VAR_KEYWORD
    description: str | None = None  # Parsed from docstring

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"name": self.name, "required": self.required, "kind": self.kind}
        if self.type_hint:
            result["type"] = self.type_hint
        if self.default is not None:
            result["default"] = self.default
        if self.description:
            result["description"] = self.description
        return result


@dataclass
class Example:
    """A code example from docstring."""
    code: str
    description: str | None = None
    output: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"code": self.code}
        if self.description:
            result["description"] = self.description
        if self.output:
            result["output"] = self.output
        return result


@dataclass
class APIInfo:
    """Comprehensive API information for a target."""
    target: str
    target_type: str  # "function", "method", "class", "module"
    name: str
    module: str
    file_path: str | None = None
    line_number: int | None = None

    # Signature info
    signature: str | None = None
    parameters: list[Parameter] = field(default_factory=list)
    return_type: str | None = None
    return_description: str | None = None

    # Documentation
    summary: str | None = None  # First line of docstring
    description: str | None = None  # Full docstring body
    examples: list[Example] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    see_also: list[str] = field(default_factory=list)
    raises: list[dict[str, str]] = field(default_factory=list)  # [{"exception": "ValueError", "description": "..."}]

    # For classes
    bases: list[str] = field(default_factory=list)
    class_attributes: list[dict[str, Any]] = field(default_factory=list)
    instance_attributes: list[dict[str, Any]] = field(default_factory=list)
    methods: list[dict[str, Any]] = field(default_factory=list)
    class_methods: list[dict[str, Any]] = field(default_factory=list)
    static_methods: list[dict[str, Any]] = field(default_factory=list)
    properties: list[dict[str, Any]] = field(default_factory=list)

    # Source
    source_preview: str | None = None  # First N lines of source
    source_available: bool = False

    # Related
    related: list[dict[str, str]] = field(default_factory=list)

    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        if self.error:
            return {"status": "error", "target": self.target, "error": self.error}

        result: dict[str, Any] = {
            "status": "success",
            "target": self.target,
            "type": self.target_type,
            "name": self.name,
            "module": self.module,
        }

        if self.file_path:
            result["file_path"] = self.file_path
        if self.line_number:
            result["line_number"] = self.line_number

        # Signature
        if self.signature:
            result["signature"] = self.signature
        if self.parameters:
            result["parameters"] = [p.to_dict() for p in self.parameters]
        if self.return_type:
            result["return_type"] = self.return_type
        if self.return_description:
            result["return_description"] = self.return_description

        # Documentation
        if self.summary:
            result["summary"] = self.summary
        if self.description:
            result["description"] = self.description
        if self.examples:
            result["examples"] = [e.to_dict() for e in self.examples]
        if self.notes:
            result["notes"] = self.notes
        if self.warnings:
            result["warnings"] = self.warnings
        if self.raises:
            result["raises"] = self.raises
        if self.see_also:
            result["see_also"] = self.see_also

        # Class-specific
        if self.target_type == "class":
            if self.bases:
                result["bases"] = self.bases
            if self.class_attributes:
                result["class_attributes"] = self.class_attributes
            if self.instance_attributes:
                result["instance_attributes"] = self.instance_attributes
            if self.methods:
                result["methods"] = self.methods
            if self.class_methods:
                result["class_methods"] = self.class_methods
            if self.static_methods:
                result["static_methods"] = self.static_methods
            if self.properties:
                result["properties"] = self.properties

        # Source
        result["source_available"] = self.source_available
        if self.source_preview:
            result["source_preview"] = self.source_preview

        if self.related:
            result["related"] = self.related

        return result


def get_api_info(resolved: ResolvedTarget, include_source: bool = True, source_lines: int = 50) -> APIInfo:
    """Get comprehensive API information for a resolved target."""
    info = APIInfo(
        target=resolved.original,
        target_type=resolved.target_type,
        name="",
        module=resolved.module_name or ""
    )

    if resolved.error:
        info.error = resolved.error
        return info

    target = resolved.symbol if resolved.symbol else resolved.module
    if target is None:
        info.error = "No target to inspect"
        return info

    # Basic info
    info.name = getattr(target, "__name__", str(target))
    info.module = getattr(target, "__module__", resolved.module_name or "")

    # File and line
    try:
        info.file_path = inspect.getfile(target)
        _, info.line_number = inspect.getsourcelines(target)
    except (TypeError, OSError):
        pass

    # Dispatch based on type
    if resolved.target_type == "class":
        _populate_class_info(target, info)
    elif resolved.target_type in ("function", "method"):
        _populate_function_info(target, info)
    elif resolved.target_type == "module":
        _populate_module_info(target, info)
    else:
        # Attribute or unknown
        info.summary = f"Value of type {type(target).__name__}"
        info.description = repr(target)[:500]

    # Source code
    if include_source:
        try:
            source = inspect.getsource(target)
            info.source_available = True
            lines = source.split("\n")
            if len(lines) > source_lines:
                info.source_preview = "\n".join(lines[:source_lines]) + f"\n... ({len(lines) - source_lines} more lines)"
            else:
                info.source_preview = source
        except (TypeError, OSError):
            info.source_available = False

    return info


def _populate_function_info(func: Any, info: APIInfo) -> None:
    """Populate APIInfo for a function or method."""
    # Signature
    try:
        sig = inspect.signature(func)
        info.signature = str(sig)
    except (ValueError, TypeError):
        pass

    # Type hints
    try:
        hints = get_type_hints(func)
    except Exception:
        hints = getattr(func, "__annotations__", {})

    # Parameters
    try:
        sig = inspect.signature(func)
        for name, param in sig.parameters.items():
            if name == "self":
                continue

            p = Parameter(name=name)
            p.kind = str(param.kind).split(".")[-1]
            p.required = param.default is inspect.Parameter.empty

            if param.default is not inspect.Parameter.empty:
                p.default = _safe_repr(param.default)

            if name in hints:
                p.type_hint = _type_to_str(hints[name])

            info.parameters.append(p)

        # Return type
        if "return" in hints:
            info.return_type = _type_to_str(hints["return"])
    except (ValueError, TypeError):
        pass

    # Parse docstring
    docstring = inspect.getdoc(func)
    if docstring:
        _parse_docstring(docstring, info)


def _populate_class_info(cls: type, info: APIInfo) -> None:
    """Populate APIInfo for a class."""
    # Bases
    info.bases = [b.__name__ for b in cls.__bases__ if b is not object]

    # __init__ signature
    if hasattr(cls, "__init__"):
        try:
            sig = inspect.signature(cls.__init__)
            # Remove 'self' from display
            params = list(sig.parameters.values())[1:]
            if params:
                info.signature = f"({', '.join(str(p) for p in params)})"
            else:
                info.signature = "()"
        except (ValueError, TypeError):
            pass

        # Get __init__ type hints for parameters
        try:
            hints = get_type_hints(cls.__init__)
        except Exception:
            hints = getattr(cls.__init__, "__annotations__", {})

        try:
            sig = inspect.signature(cls.__init__)
            for name, param in sig.parameters.items():
                if name == "self":
                    continue
                p = Parameter(name=name)
                p.kind = str(param.kind).split(".")[-1]
                p.required = param.default is inspect.Parameter.empty
                if param.default is not inspect.Parameter.empty:
                    p.default = _safe_repr(param.default)
                if name in hints:
                    p.type_hint = _type_to_str(hints[name])
                info.parameters.append(p)
        except (ValueError, TypeError):
            pass

    # Class attributes from annotations
    annotations = getattr(cls, "__annotations__", {})
    for name, type_hint in annotations.items():
        if not name.startswith("_"):
            attr_info: dict[str, Any] = {"name": name, "type": _type_to_str(type_hint)}
            if hasattr(cls, name):
                attr_info["default"] = _safe_repr(getattr(cls, name))
            info.class_attributes.append(attr_info)

    # Methods and properties
    for name in dir(cls):
        if name.startswith("_") and not name.startswith("__"):
            continue
        if name.startswith("__") and name not in ("__init__", "__call__", "__enter__", "__exit__", "__iter__", "__next__", "__getitem__", "__setitem__", "__len__", "__contains__"):
            continue

        try:
            obj = getattr(cls, name)
        except AttributeError:
            continue

        # Determine where it's defined
        defined_in = None
        for klass in cls.__mro__:
            if name in klass.__dict__:
                defined_in = klass.__name__
                break

        if isinstance(obj, property):
            prop_info: dict[str, Any] = {"name": name, "has_setter": obj.fset is not None}
            if defined_in:
                prop_info["defined_in"] = defined_in
            if obj.fget and obj.fget.__doc__:
                prop_info["description"] = _first_line(obj.fget.__doc__)
            info.properties.append(prop_info)

        elif isinstance(obj, classmethod) or (hasattr(obj, "__self__") and obj.__self__ is cls):
            method_info = _get_method_summary(obj, name, defined_in)
            info.class_methods.append(method_info)

        elif isinstance(obj, staticmethod):
            method_info = _get_method_summary(obj.__func__ if hasattr(obj, "__func__") else obj, name, defined_in)
            info.static_methods.append(method_info)

        elif callable(obj) and name != "__init__":
            method_info = _get_method_summary(obj, name, defined_in)
            info.methods.append(method_info)

    # Parse class docstring
    docstring = inspect.getdoc(cls)
    if docstring:
        _parse_docstring(docstring, info)


def _populate_module_info(module: Any, info: APIInfo) -> None:
    """Populate APIInfo for a module."""
    info.summary = _first_line(module.__doc__) if module.__doc__ else None
    info.description = module.__doc__

    # Find related items (public classes and functions)
    for name in dir(module):
        if name.startswith("_"):
            continue
        try:
            obj = getattr(module, name)
        except AttributeError:
            continue

        obj_module = getattr(obj, "__module__", None)
        if obj_module != module.__name__:
            continue  # Skip re-exports

        if isinstance(obj, type):
            info.related.append({
                "name": name,
                "type": "class",
                "summary": _first_line(obj.__doc__) if obj.__doc__ else None
            })
        elif callable(obj):
            info.related.append({
                "name": name,
                "type": "function",
                "summary": _first_line(obj.__doc__) if obj.__doc__ else None
            })


def _get_method_summary(method: Any, name: str, defined_in: str | None) -> dict[str, Any]:
    """Get a summary dict for a method."""
    result: dict[str, Any] = {"name": name}

    try:
        sig = inspect.signature(method)
        # Remove 'self' or 'cls' from display
        params = [p for p in sig.parameters.values() if p.name not in ("self", "cls")]
        if params:
            result["signature"] = f"({', '.join(str(p) for p in params)})"
        else:
            result["signature"] = "()"
    except (ValueError, TypeError):
        pass

    if defined_in:
        result["defined_in"] = defined_in

    doc = inspect.getdoc(method)
    if doc:
        result["description"] = _first_line(doc)

    return result


def _parse_docstring(docstring: str, info: APIInfo) -> None:
    """Parse a docstring and populate APIInfo fields.

    Handles Google, NumPy, and Sphinx docstring styles.
    """
    lines = docstring.strip().split("\n")
    if not lines:
        return

    # First line is summary
    info.summary = lines[0].strip()

    # Rest is description until we hit a section
    description_lines = []
    current_section = None
    section_content: list[str] = []
    param_descriptions: dict[str, str] = {}

    i = 1
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Check for section headers (Google/NumPy style)
        if stripped and stripped.endswith(":") and stripped[:-1] in (
            "Args", "Arguments", "Parameters", "Params",
            "Returns", "Return", "Yields", "Yield",
            "Raises", "Raise", "Exceptions",
            "Examples", "Example",
            "Notes", "Note",
            "Warnings", "Warning",
            "See Also", "References",
            "Attributes", "Other Parameters"
        ):
            # Save previous section
            _save_section(current_section, section_content, info, param_descriptions)
            current_section = stripped[:-1].lower()
            section_content = []
            i += 1
            continue

        # Check for Sphinx-style :param:, :returns:, etc.
        sphinx_match = re.match(r":(\w+)(?:\s+(\w+))?:\s*(.*)", stripped)
        if sphinx_match:
            directive, name, desc = sphinx_match.groups()
            if directive in ("param", "parameter", "arg", "argument"):
                if name:
                    param_descriptions[name] = desc
            elif directive in ("returns", "return"):
                info.return_description = desc
            elif directive in ("raises", "raise", "except", "exception"):
                info.raises.append({"exception": name or "Exception", "description": desc})
            i += 1
            continue

        if current_section is None:
            description_lines.append(line)
        else:
            section_content.append(line)

        i += 1

    # Save last section
    _save_section(current_section, section_content, info, param_descriptions)

    # Set description (excluding summary line)
    if description_lines:
        info.description = "\n".join(description_lines).strip()

    # Apply param descriptions
    for param in info.parameters:
        if param.name in param_descriptions:
            param.description = param_descriptions[param.name]


def _save_section(section: str | None, content: list[str], info: APIInfo, param_descriptions: dict[str, str]) -> None:
    """Save parsed section content to APIInfo."""
    if not section or not content:
        return

    text = "\n".join(content).strip()

    if section in ("args", "arguments", "parameters", "params"):
        # Parse parameter descriptions
        current_param = None
        current_desc: list[str] = []

        for line in content:
            # Check for new parameter (indented name followed by description)
            param_match = re.match(r"\s+(\w+)\s*(?:\([^)]+\))?\s*:\s*(.*)", line)
            if param_match:
                if current_param:
                    param_descriptions[current_param] = " ".join(current_desc).strip()
                current_param = param_match.group(1)
                current_desc = [param_match.group(2)] if param_match.group(2) else []
            elif current_param and line.strip():
                current_desc.append(line.strip())

        if current_param:
            param_descriptions[current_param] = " ".join(current_desc).strip()

    elif section in ("returns", "return"):
        info.return_description = text

    elif section in ("raises", "raise", "exceptions"):
        for line in content:
            exc_match = re.match(r"\s+(\w+)\s*:\s*(.*)", line)
            if exc_match:
                info.raises.append({"exception": exc_match.group(1), "description": exc_match.group(2)})

    elif section in ("examples", "example"):
        _parse_examples(content, info)

    elif section in ("notes", "note"):
        info.notes.append(text)

    elif section in ("warnings", "warning"):
        info.warnings.append(text)

    elif section in ("see also", "references"):
        for line in content:
            if line.strip():
                info.see_also.append(line.strip())


def _parse_examples(content: list[str], info: APIInfo) -> None:
    """Parse example code blocks from docstring."""
    current_example: list[str] = []
    current_output: list[str] = []
    in_output = False

    for line in content:
        if line.strip().startswith(">>>"):
            if current_example:
                # Save previous example
                info.examples.append(Example(
                    code="\n".join(current_example),
                    output="\n".join(current_output) if current_output else None
                ))
                current_example = []
                current_output = []

            current_example.append(line.strip()[4:])  # Remove ">>> "
            in_output = False

        elif line.strip().startswith("..."):
            current_example.append(line.strip()[4:])  # Remove "... "

        elif current_example and line.strip():
            # This is output
            current_output.append(line.strip())
            in_output = True

    # Save last example
    if current_example:
        info.examples.append(Example(
            code="\n".join(current_example),
            output="\n".join(current_output) if current_output else None
        ))


def _type_to_str(type_hint: Any) -> str:
    """Convert a type hint to a readable string."""
    if type_hint is None:
        return "None"
    if hasattr(type_hint, "__name__"):
        return type_hint.__name__
    # Handle typing generics
    s = str(type_hint)
    # Clean up typing module prefix
    s = s.replace("typing.", "")
    return s


def _safe_repr(obj: Any, max_length: int = 100) -> str:
    """Safely get repr of an object, truncating if needed."""
    try:
        r = repr(obj)
        if len(r) > max_length:
            return r[:max_length - 3] + "..."
        return r
    except Exception:
        return f"<{type(obj).__name__}>"


def _first_line(text: str | None) -> str | None:
    """Get the first line of text."""
    if not text:
        return None
    lines = text.strip().split("\n")
    return lines[0].strip() if lines else None


def search_api(module_name: str, query: str) -> dict[str, Any]:
    """Search for items in a module matching a query.

    Useful for finding the right function/class in a large library.
    """
    try:
        import importlib
        module = importlib.import_module(module_name)
    except ImportError as e:
        return {"status": "error", "module": module_name, "error": f"Cannot import module: {e}"}

    query_lower = query.lower()
    results: list[dict[str, Any]] = []

    for name in dir(module):
        if name.startswith("_"):
            continue

        # Check if name matches query
        if query_lower not in name.lower():
            continue

        try:
            obj = getattr(module, name)
        except AttributeError:
            continue

        result: dict[str, Any] = {"name": name, "full_path": f"{module_name}:{name}"}

        if isinstance(obj, type):
            result["type"] = "class"
            result["summary"] = _first_line(obj.__doc__)
        elif callable(obj):
            result["type"] = "function"
            result["summary"] = _first_line(obj.__doc__)
            try:
                result["signature"] = str(inspect.signature(obj))
            except (ValueError, TypeError):
                pass
        else:
            result["type"] = "attribute"
            result["value_type"] = type(obj).__name__

        results.append(result)

    # Sort by relevance (exact match first, then by name)
    results.sort(key=lambda x: (query_lower != x["name"].lower(), x["name"]))

    return {
        "status": "success",
        "module": module_name,
        "query": query,
        "results": results,
        "total": len(results)
    }
