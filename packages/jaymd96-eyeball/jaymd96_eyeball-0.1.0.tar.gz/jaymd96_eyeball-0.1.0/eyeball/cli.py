"""Dynamic CLI for hot-loading and testing any code in the project.

Designed for LLM consumption with structured JSON output.
"""

from __future__ import annotations

import json
import sys
from typing import Any

import click

from eyeball.analyzer import analyze_callers, analyze_dependencies, analyze_module_dependencies
from eyeball.harness import list_fixtures, run_probe
from eyeball.introspect import get_api_info, search_api
from eyeball.inspector import discover_module, inspect_target
from eyeball.resolver import resolve_target, reload_module
from eyeball.runner import exec_code, get_source, run_target
from eyeball.tester import list_test_files, run_tests


class JSONOutput:
    """Helper for consistent JSON output."""
    def __init__(self, pretty: bool = False):
        self.pretty = pretty

    def print(self, data: dict[str, Any]) -> None:
        if self.pretty:
            click.echo(json.dumps(data, indent=2, default=str))
        else:
            click.echo(json.dumps(data, default=str))


@click.group()
@click.option("--pretty", "-p", is_flag=True, help="Pretty-print JSON output")
@click.pass_context
def cli(ctx: click.Context, pretty: bool) -> None:
    """Dynamic CLI for hot-loading and testing code. All output is JSON."""
    ctx.ensure_object(dict)
    ctx.obj["output"] = JSONOutput(pretty=pretty)


@cli.command()
@click.argument("target")
@click.pass_context
def discover(ctx: click.Context, target: str) -> None:
    """List all public classes and functions in a module."""
    output: JSONOutput = ctx.obj["output"]
    resolved = resolve_target(target)
    result = discover_module(resolved)
    output.print(result)
    sys.exit(0 if result.get("status") == "success" else 1)


@cli.command()
@click.argument("target")
@click.pass_context
def inspect(ctx: click.Context, target: str) -> None:
    """Get detailed information about a module, class, or function."""
    output: JSONOutput = ctx.obj["output"]
    resolved = resolve_target(target)
    result = inspect_target(resolved)
    output.print(result)
    sys.exit(0 if result.get("status") == "success" else 1)


@cli.command()
@click.argument("target")
@click.option("--args", "-a", "args_json", default="[]", help="JSON array of positional arguments")
@click.option("--kwargs", "-k", "kwargs_json", default="{}", help="JSON object of keyword arguments")
@click.pass_context
def run(ctx: click.Context, target: str, args_json: str, kwargs_json: str) -> None:
    """Execute a function or instantiate a class."""
    output: JSONOutput = ctx.obj["output"]

    try:
        args = json.loads(args_json)
        if not isinstance(args, list):
            args = [args]
    except json.JSONDecodeError as e:
        output.print({"status": "error", "error": f"Invalid JSON for --args: {e}"})
        sys.exit(1)

    try:
        kwargs = json.loads(kwargs_json)
        if not isinstance(kwargs, dict):
            output.print({"status": "error", "error": "--kwargs must be a JSON object"})
            sys.exit(1)
    except json.JSONDecodeError as e:
        output.print({"status": "error", "error": f"Invalid JSON for --kwargs: {e}"})
        sys.exit(1)

    resolved = resolve_target(target)
    result = run_target(resolved, args=args, kwargs=kwargs)
    output.print(result)
    sys.exit(0 if result.get("status") == "success" else 1)


@cli.command("exec")
@click.argument("code")
@click.pass_context
def exec_command(ctx: click.Context, code: str) -> None:
    """Execute arbitrary Python code."""
    output: JSONOutput = ctx.obj["output"]
    result = exec_code(code)
    output.print(result)
    sys.exit(0 if result.get("status") == "success" else 1)


@cli.command()
@click.argument("target")
@click.option("--discover", "-d", "discover_only", is_flag=True, help="Just list tests, don't run")
@click.option("--verbose", "-v", is_flag=True, help="Include full stdout/stderr")
@click.option("--filter", "-k", "filter_expr", help="Pytest -k filter expression")
@click.option("--markers", "-m", help="Pytest markers to filter by")
@click.option("--coverage", is_flag=True, help="Include coverage report")
@click.option("--failed", "-f", "failed_only", is_flag=True, help="Run only previously failed tests")
@click.option("--timeout", "-t", default=300, help="Test timeout in seconds")
@click.pass_context
def test(ctx: click.Context, target: str, discover_only: bool, verbose: bool, filter_expr: str | None, markers: str | None, coverage: bool, failed_only: bool, timeout: int) -> None:
    """Run tests for a module, class, or test file."""
    output: JSONOutput = ctx.obj["output"]
    result = run_tests(target=target, discover_only=discover_only, verbose=verbose, filter_expr=filter_expr, markers=markers, coverage=coverage, failed_only=failed_only, timeout=timeout)
    output.print(result)
    status = result.get("status", "error")
    sys.exit(0 if status == "success" else (1 if status == "failed" else 2))


@cli.command()
@click.argument("target")
@click.pass_context
def source(ctx: click.Context, target: str) -> None:
    """Show source code of a module, class, or function."""
    output: JSONOutput = ctx.obj["output"]
    resolved = resolve_target(target)
    result = get_source(resolved)
    output.print(result)
    sys.exit(0 if result.get("status") == "success" else 1)


@cli.command()
@click.argument("module_name")
@click.pass_context
def reload(ctx: click.Context, module_name: str) -> None:
    """Reload a module after making changes."""
    output: JSONOutput = ctx.obj["output"]
    resolved = reload_module(module_name)
    if resolved.error:
        output.print({"status": "error", "module": module_name, "error": resolved.error})
        sys.exit(1)
    output.print({"status": "success", "module": module_name, "file_path": str(resolved.file_path) if resolved.file_path else None})
    sys.exit(0)


@cli.command("list-tests")
@click.option("--pattern", "-P", help="Filter test files by pattern")
@click.pass_context
def list_tests_command(ctx: click.Context, pattern: str | None) -> None:
    """List all test files in the project."""
    output: JSONOutput = ctx.obj["output"]
    result = list_test_files(pattern)
    output.print(result)
    sys.exit(0 if result.get("status") == "success" else 1)


@cli.command()
@click.argument("code")
@click.option("--setup", "-s", help="Setup code to run before the probe")
@click.option("--patch", "-P", "patches", multiple=True, help="Patch spec: 'module.attr=value'")
@click.option("--fixture", "-f", "fixtures", multiple=True, help="Fixture to load (can repeat)")
@click.option("--timeout", "-t", default=30.0, help="Execution timeout in seconds")
@click.pass_context
def probe(ctx: click.Context, code: str, setup: str | None, patches: tuple[str, ...], fixtures: tuple[str, ...], timeout: float) -> None:
    """Run a quick verification probe with assertions.

    Lightweight alternative to full pytest for rapid iteration.
    Use # @check: comments to label individual checks.

    Examples:
        eyeball probe "assert 1 + 1 == 2"
        eyeball probe --fixture mocks "assert Mock is not None"
        eyeball probe --patch "mypackage.config.DEBUG=True" "from mypackage.config import settings; assert settings.DEBUG"
    """
    output: JSONOutput = ctx.obj["output"]
    result = run_probe(code=code, setup=setup, patches=list(patches) if patches else None, fixtures=list(fixtures) if fixtures else None, timeout=timeout)
    output.print(result.to_dict())
    sys.exit(0 if result.status == "success" else (1 if result.status == "failed" else 2))


@cli.command("fixtures")
@click.pass_context
def list_fixtures_command(ctx: click.Context) -> None:
    """List available fixtures for probes."""
    output: JSONOutput = ctx.obj["output"]
    result = list_fixtures()
    output.print(result)
    sys.exit(0)


@cli.command()
@click.argument("target")
@click.pass_context
def deps(ctx: click.Context, target: str) -> None:
    """Analyze dependencies of a function, method, or class using AST.

    Shows what a target imports, calls, instantiates, and references.

    Examples:
        eyeball deps mypackage.models:User
        eyeball deps mypackage.models:User.validate
        eyeball deps mypackage.utils:process_data
    """
    output: JSONOutput = ctx.obj["output"]
    resolved = resolve_target(target)
    result = analyze_dependencies(resolved)
    output.print(result.to_dict())
    sys.exit(0 if result.error is None else 1)


@cli.command()
@click.argument("target")
@click.pass_context
def callers(ctx: click.Context, target: str) -> None:
    """Find all references to a target (reverse dependency analysis).

    Searches the codebase for imports and usages of the target.

    Examples:
        eyeball callers mypackage.models:User
        eyeball callers mypackage.auth:authenticate
    """
    output: JSONOutput = ctx.obj["output"]
    resolved = resolve_target(target)
    result = analyze_callers(resolved)
    output.print(result)
    sys.exit(0 if result.get("status") == "success" else 1)


@cli.command("module-deps")
@click.argument("target")
@click.pass_context
def module_deps(ctx: click.Context, target: str) -> None:
    """Analyze all imports in a module.

    Categorizes imports into stdlib, third-party, and local.

    Examples:
        eyeball module-deps mypackage.models
        eyeball module-deps mypackage.utils
    """
    output: JSONOutput = ctx.obj["output"]
    resolved = resolve_target(target)
    result = analyze_module_dependencies(resolved)
    output.print(result)
    sys.exit(0 if result.get("status") == "success" else 1)


@cli.command()
@click.argument("target")
@click.option("--source/--no-source", default=True, help="Include source code preview")
@click.option("--source-lines", "-n", default=50, help="Number of source lines to include")
@click.pass_context
def api(ctx: click.Context, target: str, source: bool, source_lines: int) -> None:
    """Get comprehensive API documentation for any target.

    Shows signatures, parameters with types, docstrings, examples,
    and source code. Works on your code and third-party libraries.

    Great for verifying correct usage of functions and classes.

    Examples:
        eyeball api requests:Session.get
        eyeball api pydantic:BaseModel
        eyeball api pandas:DataFrame.merge
        eyeball api mypackage.utils:process_data
    """
    output: JSONOutput = ctx.obj["output"]
    resolved = resolve_target(target)
    result = get_api_info(resolved, include_source=source, source_lines=source_lines)
    output.print(result.to_dict())
    sys.exit(0 if result.error is None else 1)


@cli.command("search-api")
@click.argument("module")
@click.argument("query")
@click.pass_context
def search_api_command(ctx: click.Context, module: str, query: str) -> None:
    """Search for items in a module by name.

    Useful for finding the right function/class in a large library.

    Examples:
        eyeball search-api requests get
        eyeball search-api pandas merge
        eyeball search-api sqlalchemy session
    """
    output: JSONOutput = ctx.obj["output"]
    result = search_api(module, query)
    output.print(result)
    sys.exit(0 if result.get("status") == "success" else 1)


@cli.command()
@click.pass_context
def help_json(ctx: click.Context) -> None:
    """Output help information as JSON for LLM consumption."""
    output: JSONOutput = ctx.obj["output"]
    commands = {
        "discover": {
            "description": "List all public classes and functions in a module",
            "usage": "eyeball discover <module>",
            "examples": ["eyeball discover mypackage.models", "eyeball discover mypackage.utils"]
        },
        "inspect": {
            "description": "Get detailed information about a module, class, or function",
            "usage": "eyeball inspect <target>",
            "examples": ["eyeball inspect mypackage.models:User", "eyeball inspect mypackage.utils:parse_config"]
        },
        "run": {
            "description": "Execute a function or instantiate a class",
            "usage": "eyeball run <target> --args '[...]' --kwargs '{...}'",
            "examples": ["eyeball run mypackage.models:User --kwargs '{\"name\": \"alice\", \"email\": \"alice@example.com\"}'"]
        },
        "exec": {
            "description": "Execute arbitrary Python code",
            "usage": "eyeball exec '<code>'",
            "examples": ["eyeball exec 'from mypackage.models import User; print(User.__annotations__)'"]
        },
        "test": {
            "description": "Run tests for a module with structured output",
            "usage": "eyeball test <target> [--discover] [--verbose] [--filter <expr>]",
            "examples": ["eyeball test mypackage.models", "eyeball test mypackage.auth --discover", "eyeball test tests/test_models.py -v"]
        },
        "source": {
            "description": "Show source code of a target",
            "usage": "eyeball source <target>",
            "examples": ["eyeball source mypackage.models:User"]
        },
        "reload": {
            "description": "Reload a module after making changes",
            "usage": "eyeball reload <module>",
            "examples": ["eyeball reload mypackage.models"]
        },
        "list-tests": {
            "description": "List all test files in the project",
            "usage": "eyeball list-tests [--pattern <pattern>]",
            "examples": ["eyeball list-tests", "eyeball list-tests --pattern auth"]
        },
        "probe": {
            "description": "Run quick verification probes with assertions (Knuth-style dogfooding)",
            "usage": "eyeball probe '<code>' [--setup '<setup>'] [--fixture <name>] [--patch 'module.attr=value']",
            "examples": ["eyeball probe 'assert 1 + 1 == 2'", "eyeball probe --fixture mocks 'assert Mock is not None'"]
        },
        "fixtures": {
            "description": "List available fixtures for probes",
            "usage": "eyeball fixtures",
            "examples": ["eyeball fixtures"]
        },
        "deps": {
            "description": "Analyze dependencies of a function, method, or class using AST",
            "usage": "eyeball deps <target>",
            "examples": ["eyeball deps mypackage.models:User", "eyeball deps mypackage.utils:parse_config"]
        },
        "callers": {
            "description": "Find all references to a target (reverse dependency analysis)",
            "usage": "eyeball callers <target>",
            "examples": ["eyeball callers mypackage.models:User", "eyeball callers mypackage.auth:authenticate"]
        },
        "module-deps": {
            "description": "Analyze all imports in a module (categorized by stdlib/third-party/local)",
            "usage": "eyeball module-deps <module>",
            "examples": ["eyeball module-deps mypackage.models", "eyeball module-deps mypackage.utils"]
        },
        "api": {
            "description": "Get comprehensive API documentation for any target (works on third-party libs)",
            "usage": "eyeball api <target> [--source/--no-source] [--source-lines N]",
            "examples": ["eyeball api requests:Session.get", "eyeball api pydantic:BaseModel", "eyeball api pandas:DataFrame.merge"]
        },
        "search-api": {
            "description": "Search for items in a module by name",
            "usage": "eyeball search-api <module> <query>",
            "examples": ["eyeball search-api requests get", "eyeball search-api pandas merge"]
        },
    }
    output.print({
        "status": "success",
        "cli": "eyeball",
        "description": "Dynamic CLI for hot-loading and testing any Python code. All output is JSON.",
        "commands": commands,
        "global_options": {"--pretty, -p": "Pretty-print JSON output"},
        "configuration": {
            "description": "Configure via pyproject.toml [tool.eyeball] or eyeball.toml",
            "options": {
                "package_name": "Your package name (auto-detected from project.name)",
                "tests_dir": "Test directory (default: 'tests')",
                "fixtures_module": "Module path for custom fixtures (e.g., 'mypackage.fixtures')"
            }
        }
    })
    sys.exit(0)


def main() -> None:
    """Entry point for eyeball."""
    cli()


if __name__ == "__main__":
    main()
