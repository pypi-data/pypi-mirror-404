"""Tests for type checking functionality."""

import pytest
from fishertools.validation import validate_types, ValidationError


class TestValidateTypes:
    """Tests for validate_types decorator."""

    def test_correct_types(self):
        """Test function with correct types."""

        @validate_types
        def add(a: int, b: int) -> int:
            return a + b

        result = add(1, 2)
        assert result == 3

    def test_incorrect_argument_type(self):
        """Test function with incorrect argument type."""

        @validate_types
        def add(a: int, b: int) -> int:
            return a + b

        with pytest.raises(ValidationError):
            add("1", 2)

    def test_incorrect_return_type(self):
        """Test function with incorrect return type."""

        @validate_types
        def get_string() -> str:
            return 123

        with pytest.raises(ValidationError):
            get_string()

    def test_multiple_arguments(self):
        """Test function with multiple arguments."""

        @validate_types
        def create_user(name: str, age: int, active: bool) -> dict:
            return {"name": name, "age": age, "active": active}

        result = create_user("Alice", 25, True)
        assert result["name"] == "Alice"
        assert result["age"] == 25

    def test_keyword_arguments(self):
        """Test function with keyword arguments."""

        @validate_types
        def greet(name: str, greeting: str = "Hello") -> str:
            return f"{greeting}, {name}!"

        result = greet("Alice", greeting="Hi")
        assert "Hi" in result

    def test_keyword_argument_wrong_type(self):
        """Test keyword argument with wrong type."""

        @validate_types
        def greet(name: str, greeting: str = "Hello") -> str:
            return f"{greeting}, {name}!"

        with pytest.raises(ValidationError):
            greet("Alice", greeting=123)

    def test_no_type_hints(self):
        """Test function without type hints."""

        @validate_types
        def add(a, b):
            return a + b

        # Should work without type hints
        result = add(1, 2)
        assert result == 3

    def test_partial_type_hints(self):
        """Test function with partial type hints."""

        @validate_types
        def add(a: int, b) -> int:
            return a + b

        result = add(1, 2)
        assert result == 3

    def test_preserves_function_name(self):
        """Test that decorator preserves function name."""

        @validate_types
        def my_function(x: int) -> int:
            return x * 2

        assert my_function.__name__ == "my_function"

    def test_preserves_docstring(self):
        """Test that decorator preserves docstring."""

        @validate_types
        def my_function(x: int) -> int:
            """Multiply by 2."""
            return x * 2

        assert "Multiply by 2" in my_function.__doc__
