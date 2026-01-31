"""Configuration detection for eyeball.

Automatically detects project settings from pyproject.toml or eyeball.toml.
"""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None  # type: ignore


@lru_cache(maxsize=1)
def find_project_root() -> Path:
    """Find the project root by looking for pyproject.toml."""
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / "pyproject.toml").exists():
            return parent
        if (parent / "eyeball.toml").exists():
            return parent
    return current


@lru_cache(maxsize=1)
def get_config() -> dict[str, Any]:
    """Load eyeball configuration from pyproject.toml or eyeball.toml."""
    project_root = find_project_root()
    config: dict[str, Any] = {
        "package_name": None,
        "tests_dir": "tests",
        "fixtures_module": None,
    }

    # Try pyproject.toml first
    pyproject_path = project_root / "pyproject.toml"
    if pyproject_path.exists() and tomllib:
        try:
            with open(pyproject_path, "rb") as f:
                pyproject = tomllib.load(f)

            # Check for [tool.eyeball] section
            eyeball_config = pyproject.get("tool", {}).get("eyeball", {})
            if eyeball_config:
                config.update(eyeball_config)

            # Auto-detect package name from project metadata if not explicitly set
            if not config["package_name"]:
                project_name = pyproject.get("project", {}).get("name")
                if project_name:
                    # Convert package name (my-package) to module name (my_package)
                    config["package_name"] = project_name.replace("-", "_")

        except Exception:
            pass

    # Try eyeball.toml as override
    eyeball_path = project_root / "eyeball.toml"
    if eyeball_path.exists() and tomllib:
        try:
            with open(eyeball_path, "rb") as f:
                eyeball_config = tomllib.load(f)
            config.update(eyeball_config)
        except Exception:
            pass

    return config


def get_package_name() -> str | None:
    """Get the configured package name."""
    return get_config().get("package_name")


def get_tests_dir() -> str:
    """Get the configured tests directory."""
    return get_config().get("tests_dir", "tests")


def get_fixtures_module() -> str | None:
    """Get the configured fixtures module path."""
    return get_config().get("fixtures_module")


def clear_config_cache() -> None:
    """Clear cached configuration (useful for testing)."""
    find_project_root.cache_clear()
    get_config.cache_clear()
