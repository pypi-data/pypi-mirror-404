"""Tests for visualization module."""

import pytest
from fishertools.visualization import visualize, Visualizer


class TestVisualizeList:
    """Tests for list visualization."""

    def test_visualize_simple_list(self):
        """Test visualizing a simple list."""
        result = visualize([1, 2, 3])
        assert "[0] → 1" in result
        assert "[1] → 2" in result
        assert "[2] → 3" in result

    def test_visualize_empty_list(self):
        """Test visualizing an empty list."""
        result = visualize([])
        assert "[]" in result

    def test_visualize_list_with_strings(self):
        """Test visualizing a list with strings."""
        result = visualize(["a", "b", "c"])
        assert "[0] → 'a'" in result
        assert "[1] → 'b'" in result
        assert "[2] → 'c'" in result

    def test_visualize_list_with_max_items(self):
        """Test visualizing a list with max_items limit."""
        result = visualize([1, 2, 3, 4, 5], max_items=3)
        assert "[0] → 1" in result
        assert "[1] → 2" in result
        assert "[2] → 3" in result
        assert "2 more items" in result


class TestVisualizeDictionary:
    """Tests for dictionary visualization."""

    def test_visualize_simple_dict(self):
        """Test visualizing a simple dictionary."""
        result = visualize({"name": "Alice", "age": 25})
        assert "'name' → 'Alice'" in result
        assert "'age' → 25" in result

    def test_visualize_empty_dict(self):
        """Test visualizing an empty dictionary."""
        result = visualize({})
        assert "{}" in result

    def test_visualize_dict_with_max_items(self):
        """Test visualizing a dictionary with max_items limit."""
        data = {"a": 1, "b": 2, "c": 3, "d": 4}
        result = visualize(data, max_items=2)
        assert "1 more items" in result or "2 more items" in result


class TestVisualizeNested:
    """Tests for nested structure visualization."""

    def test_visualize_nested_list(self):
        """Test visualizing nested lists."""
        data = [[1, 2], [3, 4]]
        result = visualize(data)
        assert "1" in result
        assert "2" in result
        assert "3" in result
        assert "4" in result

    def test_visualize_nested_dict(self):
        """Test visualizing nested dictionaries."""
        data = {"user": {"name": "Alice", "age": 25}}
        result = visualize(data)
        assert "user" in result
        assert "name" in result
        assert "Alice" in result

    def test_visualize_mixed_nested(self):
        """Test visualizing mixed nested structures."""
        data = {"users": [{"name": "Alice"}, {"name": "Bob"}]}
        result = visualize(data)
        assert "users" in result
        assert "Alice" in result
        assert "Bob" in result


class TestVisualizer:
    """Tests for Visualizer class."""

    def test_visualizer_initialization(self):
        """Test Visualizer initialization."""
        viz = Visualizer(colors=True, max_depth=3, max_items=10)
        assert viz.colors is True
        assert viz.max_depth == 3
        assert viz.max_items == 10

    def test_visualizer_visualize_method(self):
        """Test Visualizer.visualize method."""
        viz = Visualizer()
        result = viz.visualize([1, 2, 3], title="Numbers")
        assert "Numbers" in result
        assert "[0] → 1" in result

    def test_visualizer_with_title(self):
        """Test visualization with title."""
        result = visualize([1, 2, 3], title="My List")
        assert "My List" in result


class TestVisualizationEdgeCases:
    """Tests for edge cases."""

    def test_visualize_none(self):
        """Test visualizing None."""
        result = visualize(None)
        assert "None" in result

    def test_visualize_boolean(self):
        """Test visualizing boolean values."""
        result = visualize(True)
        assert "True" in result

    def test_visualize_float(self):
        """Test visualizing float values."""
        result = visualize(3.14)
        assert "3.14" in result

    def test_visualize_special_characters(self):
        """Test visualizing special characters."""
        result = visualize(["hello\nworld", "tab\there"])
        assert "hello" in result
        assert "world" in result
