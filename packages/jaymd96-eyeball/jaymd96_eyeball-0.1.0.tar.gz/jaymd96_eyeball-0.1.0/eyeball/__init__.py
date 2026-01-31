"""Dynamic CLI for hot-loading and testing any code in the project.

Designed for LLM consumption with structured JSON output.

Commands:
    discover - List modules/classes/functions in a path
    inspect  - Get signature, docstring, attributes of a target
    run      - Execute a function/method with arguments
    exec     - Run arbitrary Python code
    test     - Run pytest for a target with structured output
    source   - Show source code of a target
    probe    - Run quick verification probes (Knuth-style dogfooding)
    fixtures - List available fixtures for probes

Configuration:
    Configure via pyproject.toml [tool.eyeball] section:

    [tool.eyeball]
    package_name = "mypackage"  # Auto-detected from project.name
    tests_dir = "tests"         # Default test directory
    fixtures_module = "mypackage.fixtures"  # Custom fixtures module

    Or use a standalone eyeball.toml file with the same options.

Custom Fixtures:
    Create a fixtures module and register fixtures using the decorator:

    from eyeball.harness import Fixtures

    @Fixtures.register("my_fixture")
    def my_fixture():
        return {"key": "value", "helper": some_helper_function}
"""

from eyeball.cli import cli, main
from eyeball.harness import Fixtures, ProbeResult, Check

__all__ = ["cli", "main", "Fixtures", "ProbeResult", "Check"]
__version__ = "0.1.0"
