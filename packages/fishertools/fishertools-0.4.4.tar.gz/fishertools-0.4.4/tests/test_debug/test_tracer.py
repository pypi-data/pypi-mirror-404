"""Tests for execution tracing functionality."""

import pytest
from fishertools.debug import trace


class TestTrace:
    """Tests for trace decorator."""

    def test_trace_simple_function(self, capsys):
        """Test tracing a simple function."""

        @trace
        def add(a, b):
            return a + b

        result = add(2, 3)
        captured = capsys.readouterr()

        assert result == 5
        assert "Tracing: add" in captured.out
        assert "Result: 5" in captured.out

    def test_trace_recursive_function(self, capsys):
        """Test tracing a recursive function."""

        @trace
        def factorial(n):
            if n <= 1:
                return 1
            return n * factorial(n - 1)

        result = factorial(3)
        captured = capsys.readouterr()

        assert result == 6
        assert "Tracing: factorial" in captured.out
        assert "factorial" in captured.out

    def test_trace_preserves_function_name(self):
        """Test that decorator preserves function name."""

        @trace
        def my_function(x):
            return x * 2

        assert my_function.__name__ == "my_function"

    def test_trace_with_multiple_arguments(self, capsys):
        """Test tracing with multiple arguments."""

        @trace
        def multiply(x, y):
            return x * y

        result = multiply(3, 4)
        captured = capsys.readouterr()

        assert result == 12
        assert "Tracing: multiply" in captured.out

    def test_trace_with_exception(self, capsys):
        """Test tracing when exception occurs."""

        @trace
        def divide(a, b):
            return a / b

        with pytest.raises(ZeroDivisionError):
            divide(10, 0)

        captured = capsys.readouterr()
        assert "Tracing: divide" in captured.out
