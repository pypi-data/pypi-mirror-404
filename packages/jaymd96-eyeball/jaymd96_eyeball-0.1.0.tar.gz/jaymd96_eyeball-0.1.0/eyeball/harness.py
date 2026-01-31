"""Lightweight test harness for LLM-driven development.

Inspired by Knuth's approach to TeX - be the author and first power user.
Run quick verification probes without full pytest overhead.
"""

from __future__ import annotations

import contextlib
import importlib
import io
import sys
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable
from unittest.mock import MagicMock, Mock, patch

from eyeball.config import get_fixtures_module


@dataclass
class Check:
    """A single verification check result."""
    name: str
    passed: bool
    error: str | None = None
    error_type: str | None = None
    line: int | None = None


@dataclass
class ProbeResult:
    """Result of running a probe."""
    status: str  # "success", "failed", "error"
    checks: list[Check] = field(default_factory=list)
    stdout: str | None = None
    stderr: str | None = None
    error: str | None = None
    traceback: str | None = None

    @property
    def total(self) -> int:
        return len(self.checks)

    @property
    def passed(self) -> int:
        return sum(1 for c in self.checks if c.passed)

    @property
    def failed(self) -> int:
        return sum(1 for c in self.checks if not c.passed)

    def to_dict(self) -> dict[str, Any]:
        result = {
            "status": self.status,
            "checks": [{"name": c.name, "passed": c.passed, **({"error": c.error} if c.error else {}), **({"error_type": c.error_type} if c.error_type else {}), **({"line": c.line} if c.line else {})} for c in self.checks],
            "summary": {"total": self.total, "passed": self.passed, "failed": self.failed},
        }
        if self.stdout:
            result["stdout"] = self.stdout
        if self.stderr:
            result["stderr"] = self.stderr
        if self.error:
            result["error"] = self.error
        if self.traceback:
            result["traceback"] = self.traceback
        return result


class Fixtures:
    """Registry of reusable test fixtures."""
    _fixtures: dict[str, Callable[[], dict[str, Any]]] = {}
    _loaded_external: bool = False

    @classmethod
    def register(cls, name: str) -> Callable:
        """Decorator to register a fixture function."""
        def decorator(func: Callable[[], dict[str, Any]]) -> Callable:
            cls._fixtures[name] = func
            return func
        return decorator

    @classmethod
    def get(cls, name: str) -> dict[str, Any]:
        """Get a fixture by name, loading external fixtures if needed."""
        cls._load_external_fixtures()
        if name not in cls._fixtures:
            raise ValueError(f"Unknown fixture: {name}. Available: {list(cls._fixtures.keys())}")
        return cls._fixtures[name]()

    @classmethod
    def list(cls) -> list[str]:
        """List all available fixture names."""
        cls._load_external_fixtures()
        return list(cls._fixtures.keys())

    @classmethod
    def _load_external_fixtures(cls) -> None:
        """Load fixtures from the configured external module."""
        if cls._loaded_external:
            return
        cls._loaded_external = True

        fixtures_module = get_fixtures_module()
        if not fixtures_module:
            return

        try:
            module = importlib.import_module(fixtures_module)
            # The external module should use @Fixtures.register() decorator
            # or define a setup_fixtures() function
            if hasattr(module, "setup_fixtures"):
                module.setup_fixtures(cls)
        except ImportError:
            pass  # External fixtures module not found, that's okay

    @classmethod
    def reset(cls) -> None:
        """Reset fixtures registry (useful for testing)."""
        cls._fixtures.clear()
        cls._loaded_external = False
        # Re-register built-in fixtures
        _register_builtin_fixtures()


def _register_builtin_fixtures() -> None:
    """Register the built-in generic fixtures."""

    @Fixtures.register("mocks")
    def _mocks_fixture() -> dict[str, Any]:
        """Common mocking utilities."""
        return {"Mock": Mock, "MagicMock": MagicMock, "patch": patch}

    @Fixtures.register("async_helpers")
    def _async_helpers_fixture() -> dict[str, Any]:
        """Async testing utilities."""
        import asyncio

        def run_async(coro):
            return asyncio.run(coro)

        return {"asyncio": asyncio, "run_async": run_async}

    @Fixtures.register("temp_files")
    def _temp_files_fixture() -> dict[str, Any]:
        """Temporary file utilities."""
        import tempfile
        from pathlib import Path

        temp_dir = tempfile.mkdtemp(prefix="eyeball_probe_")

        def temp_file(name: str, content: str = "") -> Path:
            path = Path(temp_dir) / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            return path

        return {"temp_dir": Path(temp_dir), "temp_file": temp_file, "Path": Path}


# Register built-in fixtures on module load
_register_builtin_fixtures()


def parse_checks(code: str) -> list[tuple[str, int]]:
    """Parse check annotations from code. Format: # @check: description"""
    checks = []
    for i, line in enumerate(code.split("\n"), 1):
        stripped = line.strip()
        if stripped.startswith("# @check:"):
            checks.append((stripped[9:].strip(), i))
    return checks if checks else [("probe", 1)]


def apply_patches(patch_specs: list[str], namespace: dict[str, Any]) -> list[Any]:
    """Apply monkey patches from spec strings. Format: 'module.path.attr=value'"""
    active_patches = []
    for spec in patch_specs:
        if "=" not in spec:
            continue
        target, value_str = spec.split("=", 1)
        target, value_str = target.strip(), value_str.strip()
        try:
            value = eval(value_str, namespace)
        except Exception:
            value = value_str
        parts = target.rsplit(".", 1)
        if len(parts) == 2:
            module_path, attr = parts
            p = patch(f"{module_path}.{attr}", value)
            p.start()
            active_patches.append(p)
    return active_patches


def run_probe(code: str, setup: str | None = None, patches: list[str] | None = None, fixtures: list[str] | None = None, timeout: float = 30.0) -> ProbeResult:
    """Run a verification probe."""
    result = ProbeResult(status="success")
    namespace: dict[str, Any] = {"__builtins__": __builtins__, "Mock": Mock, "MagicMock": MagicMock, "patch": patch}

    for fixture_name in (fixtures or []):
        try:
            namespace.update(Fixtures.get(fixture_name))
        except ValueError as e:
            result.status = "error"
            result.error = str(e)
            return result

    active_patches = []
    if patches:
        try:
            active_patches = apply_patches(patches, namespace)
        except Exception as e:
            result.status = "error"
            result.error = f"Failed to apply patches: {e}"
            return result

    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    try:
        with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
            if setup:
                try:
                    exec(setup, namespace)
                except Exception as e:
                    result.status = "error"
                    result.error = f"Setup failed: {e}"
                    result.traceback = traceback.format_exc()
                    return result

            checks = parse_checks(code)

            try:
                exec(code, namespace)
                for name, line in checks:
                    result.checks.append(Check(name=name, passed=True, line=line))
            except AssertionError as e:
                tb = traceback.extract_tb(sys.exc_info()[2])
                fail_line = tb[-1].lineno if tb else None

                for name, line in checks:
                    if fail_line and line <= fail_line:
                        if line == fail_line or checks.index((name, line)) == len(checks) - 1:
                            result.checks.append(Check(name=name, passed=False, error=str(e) or "Assertion failed", error_type="AssertionError", line=fail_line))
                            result.status = "failed"
                        else:
                            result.checks.append(Check(name=name, passed=True, line=line))
                    else:
                        result.checks.append(Check(name=name, passed=False, error="Not reached (earlier assertion failed)", line=line))

            except Exception as e:
                result.status = "error"
                result.error = f"{type(e).__name__}: {e}"
                result.traceback = traceback.format_exc()
    finally:
        for p in active_patches:
            p.stop()

    result.stdout = stdout_capture.getvalue() or None
    result.stderr = stderr_capture.getvalue() or None
    return result


def list_fixtures() -> dict[str, Any]:
    """List available fixtures with descriptions."""
    fixtures_info = []
    for name in Fixtures.list():
        func = Fixtures._fixtures[name]
        doc = func.__doc__ or "No description"
        try:
            provides = list(func().keys())
        except Exception:
            provides = ["<error loading>"]
        fixtures_info.append({"name": name, "description": doc.strip().split("\n")[0], "provides": provides})
    return {"status": "success", "fixtures": fixtures_info, "total": len(fixtures_info)}
