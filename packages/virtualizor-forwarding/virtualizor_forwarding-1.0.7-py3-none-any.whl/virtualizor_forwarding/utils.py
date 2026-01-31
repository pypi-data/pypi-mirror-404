"""
Utility functions for Virtualizor Forwarding Tool.

Contains helper functions used across the application.
"""

from __future__ import annotations

from typing import List, Optional, TypeVar

T = TypeVar("T")


def auto_select_single(items: List[T]) -> Optional[T]:
    """
    Auto-select if list contains exactly one item.

    Args:
        items: List of items.

    Returns:
        Single item if list has exactly one, None otherwise.
    """
    if len(items) == 1:
        return items[0]
    return None


def parse_comma_ids(ids_string: str) -> List[str]:
    """
    Parse comma-separated IDs string.

    Args:
        ids_string: Comma-separated IDs (e.g., "1,2,3" or "1, 2, 3").

    Returns:
        List of trimmed ID strings.
    """
    if not ids_string:
        return []
    return [id_str.strip() for id_str in ids_string.split(",") if id_str.strip()]


def validate_port(port: int) -> bool:
    """
    Validate port number is in valid range.

    Args:
        port: Port number.

    Returns:
        True if valid (1-65535).
    """
    return isinstance(port, int) and 1 <= port <= 65535


def format_bytes(size: int) -> str:
    """
    Format bytes to human readable string.

    Args:
        size: Size in bytes.

    Returns:
        Formatted string (e.g., "1.5 MB").
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


def truncate_string(s: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    Truncate string to max length.

    Args:
        s: String to truncate.
        max_length: Maximum length.
        suffix: Suffix to add if truncated.

    Returns:
        Truncated string.
    """
    if len(s) <= max_length:
        return s
    return s[: max_length - len(suffix)] + suffix
