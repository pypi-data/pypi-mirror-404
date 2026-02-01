"""Step-by-step debugging functionality."""

import functools
import inspect
from typing import Any, Callable


def debug_step_by_step(func: Callable) -> Callable:
    """Decorator for step-by-step function execution.

    Shows each step of function execution with variable values.

    Args:
        func: Function to debug

    Returns:
        Decorated function

    Examples:
        >>> @debug_step_by_step
        ... def add(a, b):
        ...     result = a + b
        ...     return result
        >>> add(2, 3)
        🔍 Debugging: add
        Step 1: a = 2
        Step 2: b = 3
        Step 3: result = 5
        ✅ Result: 5
        5
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"\n🔍 Debugging: {func.__name__}")
        print()

        # Get function signature
        sig = inspect.signature(func)
        params = list(sig.parameters.keys())

        # Print arguments
        step = 1
        for i, arg in enumerate(args):
            if i < len(params):
                print(f"Step {step}: {params[i]} = {repr(arg)}")
                step += 1

        for key, value in kwargs.items():
            print(f"Step {step}: {key} = {repr(value)}")
            step += 1

        # Execute function
        try:
            result = func(*args, **kwargs)
            print(f"Step {step}: return {repr(result)}")
            print()
            print(f"✅ Result: {repr(result)}")
            print()
            return result
        except Exception as e:
            print(f"Step {step}: ❌ Exception: {type(e).__name__}: {e}")
            print()
            raise

    return wrapper


def set_breakpoint(message: str = "Breakpoint") -> None:
    """Set a breakpoint for debugging.

    Pauses execution and allows inspection of variables.

    Args:
        message: Message to display

    Examples:
        >>> x = 10
        >>> set_breakpoint("Check x value")
        🔴 Breakpoint: Check x value
        >>> y = x * 2
    """
    frame = inspect.currentframe()
    if frame and frame.f_back:
        caller_frame = frame.f_back
        filename = caller_frame.f_code.co_filename
        lineno = caller_frame.f_lineno
        print(f"\n🔴 Breakpoint: {message}")
        print(f"   at {filename}:{lineno}")
        print()
