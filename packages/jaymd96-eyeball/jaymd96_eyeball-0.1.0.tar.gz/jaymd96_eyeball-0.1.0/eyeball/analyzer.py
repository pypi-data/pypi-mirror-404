"""AST analysis for dependency detection in eyeball.

Analyzes Python code to find:
- Imports (modules and symbols)
- Function/method calls
- Class instantiations
- Attribute access
- Name references
"""

from __future__ import annotations

import ast
import inspect
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from eyeball.config import find_project_root, get_package_name
from eyeball.resolver import ResolvedTarget


@dataclass
class Import:
    """An import statement."""
    module: str
    name: str | None = None  # For "from X import Y", Y is the name
    alias: str | None = None
    line: int | None = None

    def to_dict(self) -> dict[str, Any]:
        result = {"module": self.module}
        if self.name:
            result["name"] = self.name
        if self.alias:
            result["alias"] = self.alias
        if self.line:
            result["line"] = self.line
        return result


@dataclass
class Call:
    """A function or method call."""
    name: str
    is_method: bool = False
    receiver: str | None = None  # For method calls, what it's called on
    line: int | None = None
    args_count: int = 0
    kwargs_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        result = {"name": self.name, "is_method": self.is_method}
        if self.receiver:
            result["receiver"] = self.receiver
        if self.line:
            result["line"] = self.line
        result["args_count"] = self.args_count
        result["kwargs_count"] = self.kwargs_count
        return result


@dataclass
class Attribute:
    """An attribute access."""
    name: str
    receiver: str
    line: int | None = None

    def to_dict(self) -> dict[str, Any]:
        result = {"name": self.name, "receiver": self.receiver}
        if self.line:
            result["line"] = self.line
        return result


@dataclass
class NameRef:
    """A name reference (variable, class, function)."""
    name: str
    line: int | None = None
    context: str = "load"  # "load", "store", "del"

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "line": self.line, "context": self.context}


@dataclass
class DependencyAnalysis:
    """Result of analyzing dependencies."""
    target: str
    target_type: str
    file_path: str | None = None
    start_line: int | None = None
    end_line: int | None = None
    imports: list[Import] = field(default_factory=list)
    calls: list[Call] = field(default_factory=list)
    attributes: list[Attribute] = field(default_factory=list)
    names: list[NameRef] = field(default_factory=list)
    instantiations: list[Call] = field(default_factory=list)  # Subset of calls that are class instantiations
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "status": "error" if self.error else "success",
            "target": self.target,
            "target_type": self.target_type,
        }
        if self.error:
            result["error"] = self.error
            return result

        if self.file_path:
            result["file_path"] = self.file_path
        if self.start_line:
            result["start_line"] = self.start_line
        if self.end_line:
            result["end_line"] = self.end_line

        result["imports"] = [i.to_dict() for i in self.imports]
        result["calls"] = [c.to_dict() for c in self.calls]
        result["instantiations"] = [c.to_dict() for c in self.instantiations]
        result["attributes"] = [a.to_dict() for a in self.attributes]
        result["names"] = [n.to_dict() for n in self.names]

        # Summary
        result["summary"] = {
            "imports": len(self.imports),
            "calls": len(self.calls),
            "instantiations": len(self.instantiations),
            "attributes": len(self.attributes),
            "names": len(self.names),
        }

        return result


class DependencyVisitor(ast.NodeVisitor):
    """AST visitor that collects dependency information."""

    def __init__(self, known_classes: set[str] | None = None):
        self.imports: list[Import] = []
        self.calls: list[Call] = []
        self.attributes: list[Attribute] = []
        self.names: list[NameRef] = []
        self.known_classes = known_classes or set()
        self._in_call = False

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.append(Import(
                module=alias.name,
                alias=alias.asname,
                line=node.lineno
            ))
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        for alias in node.names:
            self.imports.append(Import(
                module=module,
                name=alias.name,
                alias=alias.asname,
                line=node.lineno
            ))
            # Track imported names that might be classes
            if alias.name and alias.name[0].isupper():
                self.known_classes.add(alias.asname or alias.name)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        call_name = self._get_call_name(node.func)
        receiver = None
        is_method = False

        if isinstance(node.func, ast.Attribute):
            is_method = True
            receiver = self._get_receiver_name(node.func.value)

        if call_name:
            call = Call(
                name=call_name,
                is_method=is_method,
                receiver=receiver,
                line=node.lineno,
                args_count=len(node.args),
                kwargs_count=len(node.keywords)
            )
            self.calls.append(call)

        # Visit children but mark we're in a call context
        old_in_call = self._in_call
        self._in_call = True
        self.generic_visit(node)
        self._in_call = old_in_call

    def visit_Attribute(self, node: ast.Attribute) -> None:
        # Only record attribute access when not part of a call
        if not self._in_call:
            receiver = self._get_receiver_name(node.value)
            if receiver:
                self.attributes.append(Attribute(
                    name=node.attr,
                    receiver=receiver,
                    line=node.lineno
                ))
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        context = "load"
        if isinstance(node.ctx, ast.Store):
            context = "store"
        elif isinstance(node.ctx, ast.Del):
            context = "del"

        # Only track loads that aren't common builtins
        if context == "load" and node.id not in _COMMON_BUILTINS:
            self.names.append(NameRef(
                name=node.id,
                line=node.lineno,
                context=context
            ))
        self.generic_visit(node)

    def _get_call_name(self, node: ast.expr) -> str | None:
        """Extract the name being called."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        return None

    def _get_receiver_name(self, node: ast.expr) -> str | None:
        """Get the name of the receiver in an attribute access."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            base = self._get_receiver_name(node.value)
            if base:
                return f"{base}.{node.attr}"
            return node.attr
        elif isinstance(node, ast.Call):
            return "<call>"
        elif isinstance(node, ast.Subscript):
            return "<subscript>"
        return None

    def get_instantiations(self) -> list[Call]:
        """Get calls that appear to be class instantiations."""
        instantiations = []
        for call in self.calls:
            # Heuristic: if name starts with uppercase and isn't a method, likely a class
            if call.name and call.name[0].isupper() and not call.is_method:
                instantiations.append(call)
            # Or if we know it's a class from imports
            elif call.name in self.known_classes:
                instantiations.append(call)
        return instantiations


# Common builtins to filter out from name references
_COMMON_BUILTINS = {
    "True", "False", "None",
    "print", "len", "range", "str", "int", "float", "bool", "list", "dict", "set", "tuple",
    "isinstance", "issubclass", "hasattr", "getattr", "setattr", "delattr",
    "type", "super", "object", "property", "classmethod", "staticmethod",
    "open", "input", "format", "repr", "abs", "min", "max", "sum", "sorted", "reversed",
    "enumerate", "zip", "map", "filter", "any", "all", "iter", "next",
    "id", "hash", "callable", "dir", "vars", "globals", "locals",
    "Exception", "BaseException", "ValueError", "TypeError", "KeyError", "IndexError",
    "AttributeError", "ImportError", "RuntimeError", "StopIteration", "AssertionError",
}


def analyze_dependencies(resolved: ResolvedTarget) -> DependencyAnalysis:
    """Analyze dependencies of a resolved target."""
    result = DependencyAnalysis(
        target=resolved.original,
        target_type=resolved.target_type
    )

    if resolved.error:
        result.error = resolved.error
        return result

    # Get the actual object to analyze
    target = resolved.symbol if resolved.symbol else resolved.module

    if target is None:
        result.error = "No target to analyze"
        return result

    # Get source code
    try:
        source = inspect.getsource(target)
        lines, start_line = inspect.getsourcelines(target)
        file_path = inspect.getfile(target)
        result.file_path = file_path
        result.start_line = start_line
        result.end_line = start_line + len(lines) - 1
    except (TypeError, OSError) as e:
        result.error = f"Cannot get source: {e}"
        return result

    # Parse and analyze
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        result.error = f"Syntax error in source: {e}"
        return result

    # If analyzing a class, first collect known classes from module
    known_classes: set[str] = set()
    if resolved.module:
        for name in dir(resolved.module):
            obj = getattr(resolved.module, name, None)
            if isinstance(obj, type):
                known_classes.add(name)

    visitor = DependencyVisitor(known_classes)
    visitor.visit(tree)

    result.imports = visitor.imports
    result.calls = visitor.calls
    result.attributes = _dedupe_attributes(visitor.attributes)
    result.names = _dedupe_names(visitor.names)
    result.instantiations = visitor.get_instantiations()

    return result


def _dedupe_attributes(attrs: list[Attribute]) -> list[Attribute]:
    """Deduplicate attributes, keeping first occurrence."""
    seen: set[tuple[str, str]] = set()
    result = []
    for attr in attrs:
        key = (attr.receiver, attr.name)
        if key not in seen:
            seen.add(key)
            result.append(attr)
    return result


def _dedupe_names(names: list[NameRef]) -> list[NameRef]:
    """Deduplicate names, keeping first occurrence."""
    seen: set[str] = set()
    result = []
    for name in names:
        if name.name not in seen:
            seen.add(name.name)
            result.append(name)
    return result


def analyze_callers(resolved: ResolvedTarget) -> dict[str, Any]:
    """Find all files that reference a target (reverse dependency analysis).

    Searches Python files in the project for imports and usages of the target.
    """
    if resolved.error:
        return {"status": "error", "target": resolved.original, "error": resolved.error}

    target_name = resolved.symbol_name or resolved.module_name
    if not target_name:
        return {"status": "error", "target": resolved.original, "error": "Cannot determine target name"}

    # Get the simple name (last part)
    simple_name = target_name.split(".")[-1] if "." in target_name else target_name
    module_name = resolved.module_name or ""

    project_root = find_project_root()
    package_name = get_package_name()

    # Find all Python files
    search_dirs = []
    if package_name:
        pkg_dir = project_root / package_name
        if pkg_dir.exists():
            search_dirs.append(pkg_dir)
    # Also search src layout
    src_dir = project_root / "src"
    if src_dir.exists():
        search_dirs.append(src_dir)
    # Fallback to project root
    if not search_dirs:
        search_dirs.append(project_root)

    callers: list[dict[str, Any]] = []
    errors: list[str] = []

    for search_dir in search_dirs:
        for py_file in search_dir.rglob("*.py"):
            # Skip __pycache__
            if "__pycache__" in str(py_file):
                continue

            try:
                source = py_file.read_text()
                tree = ast.parse(source)
            except Exception:
                continue

            file_refs = _find_references_in_file(tree, simple_name, module_name)
            if file_refs:
                try:
                    rel_path = str(py_file.relative_to(project_root))
                except ValueError:
                    rel_path = str(py_file)

                callers.append({
                    "file": rel_path,
                    "references": file_refs
                })

    # Sort by number of references
    callers.sort(key=lambda x: len(x["references"]), reverse=True)

    return {
        "status": "success",
        "target": resolved.original,
        "target_name": simple_name,
        "module": module_name,
        "callers": callers,
        "total_files": len(callers),
        "total_references": sum(len(c["references"]) for c in callers)
    }


def _find_references_in_file(tree: ast.AST, name: str, module: str) -> list[dict[str, Any]]:
    """Find all references to a name in an AST."""
    refs: list[dict[str, Any]] = []

    class RefFinder(ast.NodeVisitor):
        def visit_Import(self, node: ast.Import) -> None:
            for alias in node.names:
                if alias.name == module or alias.name.startswith(f"{module}."):
                    refs.append({
                        "type": "import",
                        "line": node.lineno,
                        "text": f"import {alias.name}" + (f" as {alias.asname}" if alias.asname else "")
                    })
            self.generic_visit(node)

        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            node_module = node.module or ""
            if node_module == module or node_module.startswith(f"{module}."):
                for alias in node.names:
                    if alias.name == name or alias.name == "*":
                        refs.append({
                            "type": "import_from",
                            "line": node.lineno,
                            "text": f"from {node_module} import {alias.name}" + (f" as {alias.asname}" if alias.asname else "")
                        })
            # Also check if importing our name from any module
            for alias in node.names:
                if alias.name == name:
                    refs.append({
                        "type": "import_from",
                        "line": node.lineno,
                        "text": f"from {node_module} import {alias.name}" + (f" as {alias.asname}" if alias.asname else "")
                    })
            self.generic_visit(node)

        def visit_Name(self, node: ast.Name) -> None:
            if node.id == name:
                refs.append({
                    "type": "name",
                    "line": node.lineno,
                    "context": "load" if isinstance(node.ctx, ast.Load) else "store"
                })
            self.generic_visit(node)

        def visit_Attribute(self, node: ast.Attribute) -> None:
            if node.attr == name:
                refs.append({
                    "type": "attribute",
                    "line": node.lineno
                })
            self.generic_visit(node)

    finder = RefFinder()
    finder.visit(tree)

    # Dedupe by line number
    seen_lines: set[int] = set()
    unique_refs = []
    for ref in refs:
        if ref["line"] not in seen_lines:
            seen_lines.add(ref["line"])
            unique_refs.append(ref)

    return unique_refs


def analyze_module_dependencies(resolved: ResolvedTarget) -> dict[str, Any]:
    """Analyze all dependencies at the module level.

    Returns a graph of what the module imports and uses.
    """
    if resolved.error:
        return {"status": "error", "target": resolved.original, "error": resolved.error}

    if resolved.target_type != "module":
        return {"status": "error", "target": resolved.original, "error": "Target must be a module"}

    module = resolved.module
    if not module or not hasattr(module, "__file__") or not module.__file__:
        return {"status": "error", "target": resolved.original, "error": "Cannot get module source"}

    file_path = Path(module.__file__)
    try:
        source = file_path.read_text()
        tree = ast.parse(source)
    except Exception as e:
        return {"status": "error", "target": resolved.original, "error": f"Cannot parse module: {e}"}

    # Collect all imports
    imports: list[dict[str, Any]] = []

    class ImportCollector(ast.NodeVisitor):
        def visit_Import(self, node: ast.Import) -> None:
            for alias in node.names:
                imports.append({
                    "type": "import",
                    "module": alias.name,
                    "alias": alias.asname,
                    "line": node.lineno
                })
            self.generic_visit(node)

        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            module_name = node.module or ""
            for alias in node.names:
                imports.append({
                    "type": "from",
                    "module": module_name,
                    "name": alias.name,
                    "alias": alias.asname,
                    "line": node.lineno
                })
            self.generic_visit(node)

    collector = ImportCollector()
    collector.visit(tree)

    # Categorize imports
    stdlib_imports = []
    third_party = []
    local_imports = []

    package_name = get_package_name()

    for imp in imports:
        mod = imp["module"]
        # Simple heuristic for categorization
        if mod.startswith(package_name + ".") if package_name else False:
            local_imports.append(imp)
        elif "." not in mod and mod in _STDLIB_MODULES:
            stdlib_imports.append(imp)
        elif mod.split(".")[0] in _STDLIB_MODULES:
            stdlib_imports.append(imp)
        else:
            # Could be third-party or local
            if package_name and mod.startswith(package_name):
                local_imports.append(imp)
            else:
                third_party.append(imp)

    return {
        "status": "success",
        "target": resolved.original,
        "file_path": str(file_path),
        "imports": {
            "stdlib": stdlib_imports,
            "third_party": third_party,
            "local": local_imports
        },
        "summary": {
            "total": len(imports),
            "stdlib": len(stdlib_imports),
            "third_party": len(third_party),
            "local": len(local_imports)
        }
    }


# Common stdlib modules (partial list)
_STDLIB_MODULES = {
    "abc", "aifc", "argparse", "array", "ast", "asynchat", "asyncio", "asyncore",
    "atexit", "audioop", "base64", "bdb", "binascii", "binhex", "bisect", "builtins",
    "bz2", "calendar", "cgi", "cgitb", "chunk", "cmath", "cmd", "code", "codecs",
    "codeop", "collections", "colorsys", "compileall", "concurrent", "configparser",
    "contextlib", "contextvars", "copy", "copyreg", "cProfile", "crypt", "csv",
    "ctypes", "curses", "dataclasses", "datetime", "dbm", "decimal", "difflib",
    "dis", "distutils", "doctest", "email", "encodings", "enum", "errno", "faulthandler",
    "fcntl", "filecmp", "fileinput", "fnmatch", "fractions", "ftplib", "functools",
    "gc", "getopt", "getpass", "gettext", "glob", "graphlib", "grp", "gzip", "hashlib",
    "heapq", "hmac", "html", "http", "idlelib", "imaplib", "imghdr", "imp", "importlib",
    "inspect", "io", "ipaddress", "itertools", "json", "keyword", "lib2to3", "linecache",
    "locale", "logging", "lzma", "mailbox", "mailcap", "marshal", "math", "mimetypes",
    "mmap", "modulefinder", "multiprocessing", "netrc", "nis", "nntplib", "numbers",
    "operator", "optparse", "os", "ossaudiodev", "pathlib", "pdb", "pickle", "pickletools",
    "pipes", "pkgutil", "platform", "plistlib", "poplib", "posix", "posixpath", "pprint",
    "profile", "pstats", "pty", "pwd", "py_compile", "pyclbr", "pydoc", "queue", "quopri",
    "random", "re", "readline", "reprlib", "resource", "rlcompleter", "runpy", "sched",
    "secrets", "select", "selectors", "shelve", "shlex", "shutil", "signal", "site",
    "smtpd", "smtplib", "sndhdr", "socket", "socketserver", "spwd", "sqlite3", "ssl",
    "stat", "statistics", "string", "stringprep", "struct", "subprocess", "sunau",
    "symtable", "sys", "sysconfig", "syslog", "tabnanny", "tarfile", "telnetlib", "tempfile",
    "termios", "test", "textwrap", "threading", "time", "timeit", "tkinter", "token",
    "tokenize", "tomllib", "trace", "traceback", "tracemalloc", "tty", "turtle", "turtledemo",
    "types", "typing", "unicodedata", "unittest", "urllib", "uu", "uuid", "venv", "warnings",
    "wave", "weakref", "webbrowser", "winreg", "winsound", "wsgiref", "xdrlib", "xml",
    "xmlrpc", "zipapp", "zipfile", "zipimport", "zlib", "zoneinfo",
    # typing_extensions is commonly used
    "typing_extensions",
}
