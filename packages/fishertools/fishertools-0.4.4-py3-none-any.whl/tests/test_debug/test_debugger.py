"""Tests for debugging functionality."""

import pytest
from io import StringIO
import sys
from fishertools.debug import debug_step_by_step, set_breakpoint


class TestDebugStepByStep:
    """Tests for debug_step_by_step decorator."""

    def test_debug_simple_function(self, capsys):
        """Test debugging a simple function."""

        @debug_step_by_step
        def add(a, b):
            result = a + b
            return result

        result = add(2, 3)
        captured = capsys.readouterr()

        assert result == 5
        assert "Debugging: add" in captured.out
        assert "a = 2" in captured.out
        assert "b = 3" in captured.out
        assert "Result: 5" in captured.out

    def test_debug_with_multiple_arguments(self, capsys):
        """Test debugging with multiple arguments."""

        @debug_step_by_step
        def multiply(x, y, z):
            result = x * y * z
            return result

        result = multiply(2, 3, 4)
        captured = capsys.readouterr()

        assert result == 24
        assert "x = 2" in captured.out
        assert "y = 3" in captured.out
        assert "z = 4" in captured.out

    def test_debug_with_exception(self, capsys):
        """Test debugging when exception occurs."""

        @debug_step_by_step
        def divide(a, b):
            result = a / b
            return result

        with pytest.raises(ZeroDivisionError):
            divide(10, 0)

        captured = capsys.readouterr()
        assert "Exception" in captured.out

    def test_debug_preserves_function_name(self):
        """Test that decorator preserves function name."""

        @debug_step_by_step
        def my_function(x):
            return x * 2

        assert my_function.__name__ == "my_function"

    def test_debug_with_string_arguments(self, capsys):
        """Test debugging with string arguments."""

        @debug_step_by_step
        def greet(name):
            greeting = f"Hello, {name}!"
            return greeting

        result = greet("Alice")
        captured = capsys.readouterr()

        assert "Alice" in captured.out
        assert "Hello, Alice!" in captured.out


class TestSetBreakpoint:
    """Tests for set_breakpoint function."""

    def test_set_breakpoint(self, capsys):
        """Test setting a breakpoint."""
        set_breakpoint("Test breakpoint")
        captured = capsys.readouterr()

        assert "Breakpoint" in captured.out
        assert "Test breakpoint" in captured.out

    def test_set_breakpoint_with_default_message(self, capsys):
        """Test breakpoint with default message."""
        set_breakpoint()
        captured = capsys.readouterr()

        assert "Breakpoint" in captured.out
