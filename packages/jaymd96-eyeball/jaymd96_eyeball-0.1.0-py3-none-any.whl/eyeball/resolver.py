"""Target resolution for eyeball.

Handles multiple input formats:
    - File paths: "mypackage/models/entity.py"
    - Module names: "mypackage.models"
    - Symbol references: "mypackage.models:Entity"
    - Relative paths: "./my_script.py"
"""

from __future__ import annotations

import importlib
import importlib.util
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from eyeball.config import find_project_root, get_package_name, get_tests_dir


@dataclass
class ResolvedTarget:
    """Result of resolving a target string."""

    original: str
    target_type: str  # "module", "class", "function", "attribute"
    module_name: str | None = None
    module: Any = None
    symbol_name: str | None = None
    symbol: Any = None
    file_path: Path | None = None
    line_number: int | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "original": self.original,
            "target_type": self.target_type,
            "module_name": self.module_name,
            "symbol_name": self.symbol_name,
            "file_path": str(self.file_path) if self.file_path else None,
            "line_number": self.line_number,
            "error": self.error,
        }


@dataclass
class TestTarget:
    """Resolved target for test discovery."""

    original: str
    module_path: str | None = None
    symbol_name: str | None = None
    test_patterns: list[str] = field(default_factory=list)
    test_files: list[Path] = field(default_factory=list)
    error: str | None = None


def resolve_target(target: str) -> ResolvedTarget:
    """Resolve a target string to a module/symbol."""
    result = ResolvedTarget(original=target, target_type="unknown")

    try:
        if "/" in target or target.endswith(".py"):
            return _resolve_file_path(target, result)
        if ":" in target:
            return _resolve_module_symbol(target, result)
        return _resolve_module(target, result)
    except Exception as e:
        result.error = str(e)
        return result


def _resolve_file_path(target: str, result: ResolvedTarget) -> ResolvedTarget:
    """Resolve a file path to a module."""
    path = Path(target)
    if not path.is_absolute():
        project_root = find_project_root()
        path = project_root / path

    if not path.exists():
        result.error = f"File not found: {path}"
        return result

    result.file_path = path
    project_root = find_project_root()

    try:
        rel_path = path.relative_to(project_root)
        module_name = str(rel_path.with_suffix("")).replace("/", ".")
    except ValueError:
        module_name = f"_eyeball_loaded_{path.stem}"

    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        result.error = f"Cannot create module spec for: {path}"
        return result

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module

    try:
        spec.loader.exec_module(module)
    except Exception as e:
        result.error = f"Error loading module: {e}"
        return result

    result.module_name = module_name
    result.module = module
    result.target_type = "module"
    return result


def _resolve_module_symbol(target: str, result: ResolvedTarget) -> ResolvedTarget:
    """Resolve a module:symbol reference."""
    parts = target.split(":", 1)
    module_name = parts[0]
    symbol_path = parts[1]

    try:
        module = importlib.import_module(module_name)
    except ImportError as e:
        result.error = f"Cannot import module '{module_name}': {e}"
        return result

    result.module_name = module_name
    result.module = module

    if hasattr(module, "__file__") and module.__file__:
        result.file_path = Path(module.__file__)

    symbol_parts = symbol_path.split(".")
    current = module
    for part in symbol_parts:
        if not hasattr(current, part):
            result.error = f"Symbol '{part}' not found in {current}"
            return result
        current = getattr(current, part)

    result.symbol_name = symbol_path
    result.symbol = current

    if isinstance(current, type):
        result.target_type = "class"
    elif callable(current):
        result.target_type = "function"
    else:
        result.target_type = "attribute"

    try:
        import inspect
        result.line_number = inspect.getsourcelines(current)[1]
    except (TypeError, OSError):
        pass

    return result


def _resolve_module(target: str, result: ResolvedTarget) -> ResolvedTarget:
    """Resolve a plain module name."""
    try:
        module = importlib.import_module(target)
    except ImportError as e:
        result.error = f"Cannot import module '{target}': {e}"
        return result

    result.module_name = target
    result.module = module
    result.target_type = "module"

    if hasattr(module, "__file__") and module.__file__:
        result.file_path = Path(module.__file__)

    return result


def resolve_test_target(target: str) -> TestTarget:
    """Resolve a target to test file patterns."""
    result = TestTarget(original=target)
    project_root = find_project_root()
    tests_dir_name = get_tests_dir()
    tests_dir = project_root / tests_dir_name

    # Handle direct test file paths
    if target.startswith(f"{tests_dir_name}/") or target.startswith(f"{tests_dir_name}\\"):
        if "::" in target:
            file_part, test_part = target.split("::", 1)
            test_file = project_root / file_part
            if test_file.exists():
                result.test_files = [test_file]
                result.test_patterns = [f"{test_file}::{test_part}"]
        else:
            test_path = project_root / target
            if test_path.exists():
                result.test_files = [test_path]
                result.test_patterns = [str(test_path)]
            else:
                result.error = f"Test file not found: {target}"
        return result

    # Parse module:symbol format
    if ":" in target:
        module_path, symbol_name = target.split(":", 1)
        result.module_path = module_path
        result.symbol_name = symbol_name
    else:
        module_path = target
        result.module_path = module_path

    parts = module_path.split(".")

    # Strip package name prefix if it matches the configured package
    package_name = get_package_name()
    if package_name and parts and parts[0] == package_name:
        parts = parts[1:]

    if not parts:
        result.test_patterns = [str(tests_dir)]
        if tests_dir.exists():
            result.test_files = list(tests_dir.rglob("test_*.py"))
        return result

    # Build candidate test file paths
    candidates = []
    if len(parts) > 1:
        test_dir = tests_dir / "/".join(parts[:-1])
        test_file = test_dir / f"test_{parts[-1]}.py"
        candidates.append(test_file)

    candidates.append(tests_dir / f"test_{'_'.join(parts)}.py")

    if len(parts) > 1:
        candidates.append(tests_dir / parts[0] / f"test_{'_'.join(parts[1:])}.py")

    search_pattern = parts[-1]

    for candidate in candidates:
        if candidate.exists():
            result.test_files.append(candidate)

    # Fallback: search for matching test files
    if not result.test_files and tests_dir.exists():
        for test_file in tests_dir.rglob(f"*{search_pattern}*.py"):
            if test_file.name.startswith("test_"):
                result.test_files.append(test_file)

    if result.symbol_name:
        symbol_lower = result.symbol_name.lower()
        for test_file in result.test_files:
            result.test_patterns.append(f"{test_file} -k {symbol_lower}")
    else:
        result.test_patterns = [str(f) for f in result.test_files]

    if not result.test_files:
        result.error = f"No test files found for: {target}"

    return result


def reload_module(module_name: str) -> ResolvedTarget:
    """Reload a module by name."""
    result = ResolvedTarget(original=module_name, target_type="module")

    if module_name not in sys.modules:
        result.error = f"Module '{module_name}' is not loaded"
        return result

    try:
        module = sys.modules[module_name]
        importlib.reload(module)
        result.module = module
        result.module_name = module_name
        if hasattr(module, "__file__") and module.__file__:
            result.file_path = Path(module.__file__)
    except Exception as e:
        result.error = f"Failed to reload module: {e}"

    return result
