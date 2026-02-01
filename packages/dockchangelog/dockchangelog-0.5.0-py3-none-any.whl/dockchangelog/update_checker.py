"""
Check for available updates to dockchangelog.
"""

import json
import sys
from pathlib import Path
from typing import Optional, Tuple

import httpx

from . import __version__


def get_latest_version() -> Optional[str]:
    """
    Get the latest version from PyPI.
    
    Returns:
        Latest version string or None if check fails
    """
    try:
        response = httpx.get(
            "https://pypi.org/pypi/dockchangelog/json",
            timeout=2.0,
            follow_redirects=True,
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("info", {}).get("version")
    except Exception:
        # Silently fail - update check is not critical
        pass
    return None


def detect_installation_method() -> str:
    """
    Detect how dockchangelog was installed.
    
    Returns:
        Installation method: 'pipx', 'pip', 'uv', 'source', or 'unknown'
    """
    # Check if installed via pipx
    if "pipx" in sys.prefix or ".local/pipx" in sys.prefix:
        return "pipx"
    
    # Check if running from source (editable install)
    try:
        import dockchangelog
        package_path = Path(dockchangelog.__file__).parent.parent
        if (package_path / "pyproject.toml").exists():
            # Likely running from source
            return "source"
    except Exception:
        pass
    
    # Check if uv is in the path (heuristic)
    if ".venv" in sys.prefix or "uv" in sys.prefix:
        return "uv"
    
    # Default to pip
    return "pip"


def get_update_command(method: str) -> str:
    """
    Get the appropriate update command based on installation method.
    
    Args:
        method: Installation method
    
    Returns:
        Command to update the tool
    """
    commands = {
        "pipx": "pipx upgrade dockchangelog",
        "pip": "pip install --upgrade dockchangelog",
        "uv": "uv pip install --upgrade dockchangelog",
        "source": "cd /path/to/dockchangelog && git pull && pip install -e .",
    }
    return commands.get(method, "pip install --upgrade dockchangelog")


def check_for_updates() -> Optional[Tuple[str, str, str]]:
    """
    Check if an update is available.
    
    Returns:
        Tuple of (current_version, latest_version, update_command) if update available,
        None if up to date or check failed
    """
    latest = get_latest_version()
    
    if not latest:
        return None
    
    # Normalize versions for comparison (remove 'v' prefix if present)
    current = __version__.lstrip('v')
    latest = latest.lstrip('v')
    
    if current != latest:
        method = detect_installation_method()
        command = get_update_command(method)
        return (__version__, latest, command)
    
    return None
