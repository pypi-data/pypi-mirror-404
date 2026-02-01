"""
Pytest configuration and fixtures for fishertools tests.
"""

import pytest
from hypothesis import settings, Verbosity


# Configure hypothesis for property-based testing
settings.register_profile("default", max_examples=100, verbosity=Verbosity.normal)
settings.load_profile("default")


@pytest.fixture
def sample_exceptions():
    """Fixture providing common exception types for testing."""
    return [
        TypeError("'str' object cannot be interpreted as an integer"),
        ValueError("invalid literal for int() with base 10: 'abc'"),
        AttributeError("'str' object has no attribute 'append'"),
        IndexError("list index out of range"),
        KeyError("'missing_key'"),
        ImportError("No module named 'nonexistent_module'"),
        SyntaxError("invalid syntax"),
    ]