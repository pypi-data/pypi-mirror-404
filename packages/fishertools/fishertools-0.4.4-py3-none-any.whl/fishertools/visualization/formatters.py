"""Formatting functions for visualization."""

from typing import Any, Optional


def format_list(lst: list, max_items: Optional[int] = None) -> str:
    """Format a list for visualization.

    Args:
        lst: List to format
        max_items: Maximum items to show

    Returns:
        Formatted list string
    """
    if not lst:
        return "[]"

    lines = []
    items_to_show = lst if max_items is None else lst[:max_items]

    for i, item in enumerate(items_to_show):
        lines.append(f"[{i}] → {repr(item)}")

    if max_items and len(lst) > max_items:
        remaining = len(lst) - max_items
        lines.append(f"... and {remaining} more items")

    return "\n".join(lines)


def format_dict(d: dict, max_items: Optional[int] = None) -> str:
    """Format a dictionary for visualization.

    Args:
        d: Dictionary to format
        max_items: Maximum items to show

    Returns:
        Formatted dictionary string
    """
    if not d:
        return "{}"

    lines = ["{"]
    items = list(d.items())
    items_to_show = items if max_items is None else items[:max_items]

    for key, value in items_to_show:
        lines.append(f'  {repr(key)} → {repr(value)}')

    if max_items and len(items) > max_items:
        remaining = len(items) - max_items
        lines.append(f"  ... and {remaining} more items")

    lines.append("}")
    return "\n".join(lines)


def format_nested(
    data: Any, depth: int = 0, max_depth: int = 5, indent: str = "  "
) -> str:
    """Format nested data structures.

    Args:
        data: Data to format
        depth: Current depth
        max_depth: Maximum depth
        indent: Indentation string

    Returns:
        Formatted nested structure
    """
    if depth >= max_depth:
        return f"{repr(data)} [max depth reached]"

    if isinstance(data, dict):
        return _format_dict_nested(data, depth, max_depth, indent)
    elif isinstance(data, (list, tuple)):
        return _format_sequence_nested(data, depth, max_depth, indent)
    else:
        return repr(data)


def _format_dict_nested(data: dict, depth: int, max_depth: int, indent: str) -> str:
    """Format nested dictionary."""
    if not data:
        return "{}"
    
    lines = ["{"]
    for key, value in data.items():
        formatted_value = format_nested(value, depth + 1, max_depth, indent)
        lines.append(f"{indent * (depth + 1)}{repr(key)}: {formatted_value}")
    lines.append(f"{indent * depth}}}")
    return "\n".join(lines)


def _format_sequence_nested(data: Any, depth: int, max_depth: int, indent: str) -> str:
    """Format nested list or tuple."""
    if not data:
        return "[]" if isinstance(data, list) else "()"
    
    is_list = isinstance(data, list)
    lines = ["[" if is_list else "("]
    for item in data:
        formatted_item = format_nested(item, depth + 1, max_depth, indent)
        lines.append(f"{indent * (depth + 1)}{formatted_item}")
    lines.append(f"{indent * depth}]" if is_list else ")")
    return "\n".join(lines)
