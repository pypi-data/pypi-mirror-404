"""
Update checker for Virtualizor Forwarding Tool.

Checks PyPI for new versions with daily cache.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime

import requests

from . import __version__, __pypi__


# Cache file location
CACHE_DIR = Path.home() / ".cache" / "virtualizor-forwarding"
CACHE_FILE = CACHE_DIR / "update_check.json"
CACHE_EXPIRY = 86400  # 24 hours in seconds


def get_latest_version() -> Optional[str]:
    """
    Fetch latest version from PyPI.
    
    Returns:
        Latest version string or None if failed.
    """
    try:
        response = requests.get(
            f"https://pypi.org/pypi/{__pypi__}/json",
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("info", {}).get("version")
    except (requests.RequestException, json.JSONDecodeError):
        pass
    return None


def _load_cache() -> dict:
    """Load cache from file."""
    try:
        if CACHE_FILE.exists():
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except (json.JSONDecodeError, OSError):
        pass
    return {}


def _save_cache(data: dict) -> None:
    """Save cache to file."""
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except OSError:
        pass


def check_update_cached() -> Tuple[Optional[str], bool]:
    """
    Check for updates with caching (once per day).
    
    Returns:
        Tuple of (latest_version, is_new_check).
        latest_version is None if check failed or cache is valid.
        is_new_check is True if we actually checked PyPI.
    """
    cache = _load_cache()
    last_check = cache.get("last_check", 0)
    cached_version = cache.get("latest_version")
    
    # Check if cache is still valid
    if time.time() - last_check < CACHE_EXPIRY:
        return cached_version, False
    
    # Fetch new version
    latest = get_latest_version()
    if latest:
        _save_cache({
            "last_check": time.time(),
            "latest_version": latest,
            "checked_at": datetime.now().isoformat()
        })
        return latest, True
    
    return cached_version, False


def is_update_available(latest: Optional[str] = None) -> bool:
    """
    Check if update is available.
    
    Args:
        latest: Latest version to compare. If None, uses cached version.
    
    Returns:
        True if newer version is available.
    """
    if latest is None:
        latest, _ = check_update_cached()
    
    if not latest:
        return False
    
    return _compare_versions(latest, __version__) > 0


def _compare_versions(v1: str, v2: str) -> int:
    """
    Compare two version strings.
    
    Returns:
        1 if v1 > v2, -1 if v1 < v2, 0 if equal.
    """
    def parse_version(v: str) -> Tuple[int, ...]:
        try:
            return tuple(int(x) for x in v.split("."))
        except ValueError:
            return (0,)
    
    p1, p2 = parse_version(v1), parse_version(v2)
    
    # Pad shorter version with zeros
    max_len = max(len(p1), len(p2))
    p1 = p1 + (0,) * (max_len - len(p1))
    p2 = p2 + (0,) * (max_len - len(p2))
    
    if p1 > p2:
        return 1
    elif p1 < p2:
        return -1
    return 0


def get_current_version() -> str:
    """Get current installed version."""
    return __version__
