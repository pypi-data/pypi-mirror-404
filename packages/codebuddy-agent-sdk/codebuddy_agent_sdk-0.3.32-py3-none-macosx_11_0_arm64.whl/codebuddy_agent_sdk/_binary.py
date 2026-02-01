"""
Binary locator for CodeBuddy CLI.

This module provides functions to locate the CodeBuddy CLI binary.
The binary is bundled in platform-specific wheels.
"""

from __future__ import annotations

import os
import platform
import sys
from pathlib import Path

from ._errors import CLINotFoundError

__all__ = ["get_cli_path", "try_cli_path", "get_platform_info", "get_cli_version"]


# Platform mapping for goreleaser output directories (for monorepo development)
# Note: For musl (Alpine), the correct binary is bundled in the wheel at build time
_PLATFORM_DIRS: dict[tuple[str, str], str] = {
    ("Darwin", "arm64"): "darwin-arm64_bun-darwin-arm64",
    ("Darwin", "x86_64"): "darwin-x64_bun-darwin-x64",
    ("Linux", "x86_64"): "linux-x64_bun-linux-x64",
    ("Linux", "aarch64"): "linux-arm64_bun-linux-arm64",
    ("Windows", "AMD64"): "windows-x64_bun-windows-x64",
}

# Binary name per platform
_BINARY_NAMES: dict[str, str] = {
    "Darwin": "codebuddy",
    "Linux": "codebuddy",
    "Windows": "codebuddy.exe",
}


def _get_package_binary_path() -> Path | None:
    """Get the binary path bundled in the package."""
    # Binary is bundled at package_root/bin/codebuddy
    pkg_root = Path(__file__).parent
    system = platform.system()
    binary_name = _BINARY_NAMES.get(system, "codebuddy")
    bin_path = pkg_root / "bin" / binary_name

    if bin_path.exists() and bin_path.is_file():
        return bin_path

    return None


def _get_monorepo_binary_path() -> Path | None:
    """Get the binary path from monorepo development structure."""
    system = platform.system()
    machine = platform.machine()
    key = (system, machine)

    dir_name = _PLATFORM_DIRS.get(key)
    if not dir_name:
        return None

    binary_name = _BINARY_NAMES.get(system, "codebuddy")

    # Try relative to this package (agent-sdk-python -> agent-cli)
    pkg_root = Path(__file__).parent
    monorepo_path = pkg_root.parent.parent.parent / "agent-cli" / "out" / dir_name / binary_name

    if monorepo_path.exists() and monorepo_path.is_file():
        return monorepo_path

    return None


def get_cli_path() -> str:
    """
    Get the path to the CodeBuddy CLI binary.

    Resolution order:
    1. CODEBUDDY_CODE_PATH environment variable
    2. Binary bundled in the package (wheel)
    3. Monorepo development path

    Returns:
        The absolute path to the CLI binary.

    Raises:
        CLINotFoundError: If the binary cannot be found.
    """
    system = platform.system()
    machine = platform.machine()

    # 1. Environment variable takes precedence
    env_path = os.environ.get("CODEBUDDY_CODE_PATH")
    if env_path:
        path = Path(env_path)
        if path.exists():
            return str(path)
        # Warn but continue to try other methods
        print(
            f"Warning: CODEBUDDY_CODE_PATH is set to '{env_path}' but file does not exist. "
            "Falling back to other resolution methods.",
            file=sys.stderr,
        )

    # 2. Try package bundled binary
    pkg_path = _get_package_binary_path()
    if pkg_path:
        return str(pkg_path)

    # 3. Try monorepo development path
    monorepo_path = _get_monorepo_binary_path()
    if monorepo_path:
        return str(monorepo_path)

    # 4. Nothing found - raise helpful error
    supported = ", ".join(f"{s}-{m}" for s, m in _PLATFORM_DIRS)
    raise CLINotFoundError(
        f"CodeBuddy CLI binary not found for platform '{system}-{machine}'.\n\n"
        f"Possible solutions:\n"
        f"  1. Reinstall the package to get the correct platform wheel:\n"
        f"     pip install --force-reinstall codebuddy-agent-sdk\n\n"
        f"  2. Set CODEBUDDY_CODE_PATH environment variable to the CLI binary path\n\n"
        f"  3. Install the CLI separately and set the path\n\n"
        f"Supported platforms: {supported}",
        system,
        machine,
    )


def try_cli_path() -> str | None:
    """
    Try to get the CLI path without raising an exception.

    Returns:
        The CLI path if found, None otherwise.
    """
    try:
        return get_cli_path()
    except CLINotFoundError:
        return None


def get_platform_info() -> tuple[str, str]:
    """
    Get the current platform information.

    Returns:
        A tuple of (system, machine).
    """
    return platform.system(), platform.machine()


# Cached CLI version
_cached_cli_version: str | None = None


def get_cli_version(cli_path: str | None = None) -> str:
    """
    Get the version of the CodeBuddy CLI.

    Attempts to read version from multiple sources:
    1. metadata.json (for binary builds from goreleaser)
    2. package.json (for Node.js development environment)

    Args:
        cli_path: Optional CLI path. If not provided, will resolve using get_cli_path().

    Returns:
        The CLI version string, or 'unknown' if not found.
    """
    global _cached_cli_version

    if _cached_cli_version is not None:
        return _cached_cli_version

    try:
        import json
        import re

        resolved_path = Path(cli_path) if cli_path else Path(get_cli_path())
        cli_dir = resolved_path.parent
        parent_dir = cli_dir.parent

        # 1. Try metadata.json (for binary builds)
        # Binary is at: .../out/<platform>/codebuddy, metadata.json is at .../out/metadata.json
        metadata_path = parent_dir / "metadata.json"
        if metadata_path.exists():
            with open(metadata_path, encoding="utf-8") as f:
                metadata = json.load(f)
            # Extract version from tag like "@tencent-ai/codebuddy-code@2.41.6" or with suffixes
            tag = metadata.get("tag", "")
            match = re.search(r"@(\d+\.\d+\.\d+)", tag)
            if match:
                _cached_cli_version = match.group(1)
                return _cached_cli_version

        # 2. Try package.json (for Node.js development environment)
        # CLI binary is typically at: .../bin/codebuddy or .../dist/codebuddy
        package_json_path = parent_dir / "package.json"
        if not package_json_path.exists():
            # Try two levels up (for dist/codebuddy structure)
            package_json_path = parent_dir.parent / "package.json"

        if package_json_path.exists():
            with open(package_json_path, encoding="utf-8") as f:
                package_json = json.load(f)
            # Use publishConfig.customPackage.version if available (published version)
            version = (
                package_json.get("publishConfig", {}).get("customPackage", {}).get("version")
                or package_json.get("version")
            )
            if version and version != "0.0.0":
                _cached_cli_version = version
                return version
    except Exception:
        pass

    _cached_cli_version = "unknown"
    return "unknown"
