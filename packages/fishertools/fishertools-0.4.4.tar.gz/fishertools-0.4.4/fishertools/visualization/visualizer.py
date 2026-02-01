"""Core visualization functionality."""

from typing import Any, Optional
from .formatters import format_list, format_dict, format_nested


class Visualizer:
    """Visualize data structures in a human-readable format."""

    def __init__(
        self,
        colors: bool = True,
        max_depth: int = 5,
        max_items: Optional[int] = None,
    ):
        """Initialize visualizer.

        Args:
            colors: Use colored output
            max_depth: Maximum nesting depth
            max_items: Maximum items to show (None = show all)
        """
        self.colors = colors
        self.max_depth = max_depth
        self.max_items = max_items

    def visualize(self, data: Any, title: Optional[str] = None) -> str:
        """Visualize data structure.

        Args:
            data: Data to visualize
            title: Optional title

        Returns:
            Formatted visualization string
        """
        output = []

        if title:
            output.append(f"📊 {title}:")
        else:
            output.append("📊 Visualization:")

        if isinstance(data, list):
            output.append(format_list(data, self.max_items))
        elif isinstance(data, dict):
            output.append(format_dict(data, self.max_items))
        else:
            output.append(format_nested(data, depth=0, max_depth=self.max_depth))

        return "\n".join(output)

    def print(self, data: Any, title: Optional[str] = None) -> None:
        """Print visualization to console.

        Args:
            data: Data to visualize
            title: Optional title
        """
        print(self.visualize(data, title))


def visualize(
    data: Any,
    title: Optional[str] = None,
    colors: bool = True,
    max_depth: int = 5,
    max_items: Optional[int] = None,
) -> str:
    """Visualize a data structure.

    Args:
        data: Data to visualize
        title: Optional title
        colors: Use colored output
        max_depth: Maximum nesting depth
        max_items: Maximum items to show

    Returns:
        Formatted visualization string

    Examples:
        >>> visualize([1, 2, 3])
        '📊 Visualization:\\n[0] → 1\\n[1] → 2\\n[2] → 3'

        >>> visualize({"name": "Alice", "age": 25})
        '📊 Visualization:\\n{\\n  "name" → "Alice"\\n  "age" → 25\\n}'
    """
    visualizer = Visualizer(colors=colors, max_depth=max_depth, max_items=max_items)
    return visualizer.visualize(data, title)
