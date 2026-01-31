"""Pytest integration for eyeball."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from eyeball.config import find_project_root, get_package_name
from eyeball.resolver import TestTarget, resolve_test_target


def run_tests(target: str, discover_only: bool = False, verbose: bool = False, filter_expr: str | None = None, markers: str | None = None, coverage: bool = False, failed_only: bool = False, timeout: int = 300) -> dict[str, Any]:
    """Run pytest for a target with structured output."""
    resolved = resolve_test_target(target)

    if resolved.error:
        return {"status": "error", "target": target, "error": resolved.error, "suggestion": _get_suggestion(target)}

    project_root = find_project_root()

    if discover_only:
        return _discover_tests(resolved, project_root, filter_expr)

    return _run_pytest(resolved, project_root, verbose, filter_expr, markers, coverage, failed_only, timeout)


def _discover_tests(resolved: TestTarget, project_root: Path, filter_expr: str | None = None) -> dict[str, Any]:
    """Discover tests without running them."""
    cmd = [sys.executable, "-m", "pytest", "--collect-only", "-q"]

    for test_file in resolved.test_files:
        cmd.append(str(test_file))

    if filter_expr:
        cmd.extend(["-k", filter_expr])
    if resolved.symbol_name:
        cmd.extend(["-k", resolved.symbol_name.lower()])

    try:
        result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        return {"status": "error", "target": resolved.original, "error": "Test discovery timed out"}
    except Exception as e:
        return {"status": "error", "target": resolved.original, "error": f"Failed to run pytest: {e}"}

    tests = [line.strip() for line in result.stdout.strip().split("\n") if "::" in line and not line.strip().startswith(("=", "-", " "))]

    return {"status": "success", "target": resolved.original, "test_files": [str(f) for f in resolved.test_files], "tests": tests, "total": len(tests)}


def _run_pytest(resolved: TestTarget, project_root: Path, verbose: bool, filter_expr: str | None, markers: str | None, coverage: bool, failed_only: bool, timeout: int) -> dict[str, Any]:
    """Run pytest and return structured results."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json_report_path = f.name

    cmd = [sys.executable, "-m", "pytest", "--tb=short", f"--json-report-file={json_report_path}", "--json-report"]

    for test_file in resolved.test_files:
        cmd.append(str(test_file))

    if filter_expr:
        cmd.extend(["-k", filter_expr])
    elif resolved.symbol_name:
        cmd.extend(["-k", resolved.symbol_name.lower()])

    if markers:
        cmd.extend(["-m", markers])
    if failed_only:
        cmd.append("--lf")
    if coverage:
        package_name = get_package_name()
        if package_name:
            cmd.extend(["--cov", package_name, "--cov-report", "json"])
        else:
            # Fall back to covering the src directory or current directory
            cmd.extend(["--cov", ".", "--cov-report", "json"])
    if verbose:
        cmd.append("-v")

    try:
        result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"status": "error", "target": resolved.original, "error": f"Tests timed out after {timeout}s"}
    except Exception as e:
        return {"status": "error", "target": resolved.original, "error": f"Failed to run pytest: {e}"}

    report = _parse_json_report(json_report_path)

    try:
        Path(json_report_path).unlink()
    except Exception:
        pass

    if report is None:
        return _parse_stdout_results(resolved, result)

    return _format_report(resolved, report, result, verbose)


def _parse_json_report(path: str) -> dict | None:
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


def _format_report(resolved: TestTarget, report: dict, result: subprocess.CompletedProcess, verbose: bool) -> dict[str, Any]:
    """Format JSON report into our output structure."""
    summary = report.get("summary", {})
    tests = report.get("tests", [])
    passed, failed, skipped, errors = [], [], [], []

    for test in tests:
        test_info = {"test": test.get("nodeid", ""), "duration": test.get("duration", 0)}
        outcome = test.get("outcome", "")

        if outcome == "passed":
            passed.append(test_info)
        elif outcome == "failed":
            call = test.get("call", {})
            test_info["error_type"] = call.get("crash", {}).get("message", "AssertionError")
            test_info["message"] = call.get("longrepr", "")
            nodeid = test.get("nodeid", "")
            if "::" in nodeid:
                test_info["file"] = nodeid.split("::")[0]
            crash = call.get("crash", {})
            if crash.get("lineno"):
                test_info["line"] = crash.get("lineno")
            failed.append(test_info)
        elif outcome == "skipped":
            skipped.append(test_info)
        elif outcome == "error":
            test_info["error"] = test.get("setup", {}).get("longrepr", "")
            errors.append(test_info)

    status = "success" if not failed and not errors else "failed"

    output = {
        "status": status, "target": resolved.original, "test_files": [str(f) for f in resolved.test_files],
        "summary": {"total": summary.get("total", len(tests)), "passed": summary.get("passed", len(passed)), "failed": summary.get("failed", len(failed)), "skipped": summary.get("skipped", len(skipped)), "errors": summary.get("error", len(errors)), "duration_seconds": report.get("duration", 0)},
        "passed": passed[:20] if not verbose else passed, "failed": failed, "skipped": skipped[:10] if not verbose else skipped, "errors": errors,
    }

    if verbose:
        output["stdout"] = result.stdout
        output["stderr"] = result.stderr

    return output


def _parse_stdout_results(resolved: TestTarget, result: subprocess.CompletedProcess) -> dict[str, Any]:
    """Parse pytest results from stdout when JSON report unavailable."""
    stdout = result.stdout
    stderr = result.stderr
    passed = failed = skipped = errors = 0

    for line in stdout.split("\n"):
        line = line.strip()
        if "passed" in line or "failed" in line:
            matches = re.findall(r"(\d+)\s+(passed|failed|skipped|error)", line)
            for count, outcome in matches:
                if outcome == "passed":
                    passed = int(count)
                elif outcome == "failed":
                    failed = int(count)
                elif outcome == "skipped":
                    skipped = int(count)
                elif outcome == "error":
                    errors = int(count)

    total = passed + failed + skipped + errors
    status = "success" if result.returncode == 0 else "failed"

    return {"status": status, "target": resolved.original, "test_files": [str(f) for f in resolved.test_files], "summary": {"total": total, "passed": passed, "failed": failed, "skipped": skipped, "errors": errors}, "stdout": stdout, "stderr": stderr or None, "note": "JSON report unavailable, install pytest-json-report for detailed results"}


def _get_suggestion(target: str) -> str:
    if ":" in target:
        module = target.split(":")[0]
        return f"Try 'eyeball test {module}' to test the whole module"
    parts = target.split(".")
    if len(parts) > 2:
        parent = ".".join(parts[:-1])
        return f"Try 'eyeball test {parent}' to test the parent module"
    return "Check that the target module exists and has corresponding test files"


def list_test_files(pattern: str | None = None) -> dict[str, Any]:
    """List all test files in the project."""
    project_root = find_project_root()
    tests_dir = project_root / "tests"

    if not tests_dir.exists():
        return {"status": "error", "error": "No tests directory found"}

    test_files = [str(f.relative_to(project_root)) for f in tests_dir.rglob("test_*.py") if not pattern or pattern in str(f)]

    return {"status": "success", "tests_dir": str(tests_dir), "test_files": sorted(test_files), "total": len(test_files)}
