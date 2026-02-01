"""Type checking functionality."""

import functools
from typing import get_type_hints, Any
from .exceptions import ValidationError


def validate_types(func):
    """Decorator to validate function argument and return types.

    Uses type hints to validate arguments and return value.

    Args:
        func: Function to decorate

    Returns:
        Decorated function

    Raises:
        ValidationError: If type validation fails

    Examples:
        >>> @validate_types
        ... def add(a: int, b: int) -> int:
        ...     return a + b
        >>> add(1, 2)
        3
        >>> add("1", 2)  # Raises ValidationError
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Get type hints
        hints = get_type_hints(func)

        # Get function signature
        import inspect

        sig = inspect.signature(func)
        params = list(sig.parameters.keys())

        # Check argument types
        for i, arg in enumerate(args):
            if i < len(params):
                param_name = params[i]
                if param_name in hints:
                    expected_type = hints[param_name]
                    if not isinstance(arg, expected_type):
                        raise ValidationError(
                            f"Argument '{param_name}' must be {expected_type.__name__}, "
                            f"got {type(arg).__name__}"
                        )

        # Check keyword argument types
        for key, value in kwargs.items():
            if key in hints:
                expected_type = hints[key]
                if not isinstance(value, expected_type):
                    raise ValidationError(
                        f"Argument '{key}' must be {expected_type.__name__}, "
                        f"got {type(value).__name__}"
                    )

        # Call function
        result = func(*args, **kwargs)

        # Check return type
        if "return" in hints:
            expected_return_type = hints["return"]
            if not isinstance(result, expected_return_type):
                raise ValidationError(
                    f"Return value must be {expected_return_type.__name__}, "
                    f"got {type(result).__name__}"
                )

        return result

    return wrapper
