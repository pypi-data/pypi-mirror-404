"""Execution tracing functionality."""

import functools
import sys
from typing import Callable


def trace(func: Callable) -> Callable:
    """Decorator for tracing function execution.

    Shows all function calls and returns with indentation.

    Args:
        func: Function to trace

    Returns:
        Decorated function

    Examples:
        >>> @trace
        ... def fibonacci(n):
        ...     if n <= 1:
        ...         return n
        ...     return fibonacci(n-1) + fibonacci(n-2)
        >>> fibonacci(3)
        🔍 Tracing: fibonacci
        → fibonacci(3)
          → fibonacci(2)
            → fibonacci(1) = 1
            → fibonacci(0) = 0
          ← fibonacci(2) = 1
          → fibonacci(1) = 1
        ← fibonacci(3) = 2
        2
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"\n🔍 Tracing: {func.__name__}")
        print()

        # Create tracer
        call_stack = []

        def trace_calls(frame, event, arg):
            if event == "call":
                code = frame.f_code
                if code.co_name == func.__name__:
                    indent = "  " * len(call_stack)
                    args_str = _format_args(frame)
                    print(f"{indent}→ {code.co_name}({args_str})")
                    call_stack.append(code.co_name)

            elif event == "return":
                code = frame.f_code
                if code.co_name == func.__name__ and call_stack:
                    call_stack.pop()
                    indent = "  " * len(call_stack)
                    print(f"{indent}← {code.co_name}({_format_args(frame)}) = {repr(arg)}")

            return trace_calls

        # Set trace
        old_trace = sys.gettrace()
        sys.settrace(trace_calls)

        try:
            result = func(*args, **kwargs)
            print()
            print(f"✅ Result: {repr(result)}")
            print()
            return result
        finally:
            sys.settrace(old_trace)

    return wrapper


def _format_args(frame) -> str:
    """Format function arguments from frame.

    Args:
        frame: Stack frame

    Returns:
        Formatted arguments string
    """
    args = frame.f_locals
    if not args:
        return ""

    parts = []
    for key, value in args.items():
        if not key.startswith("_"):
            parts.append(f"{key}={repr(value)}")

    return ", ".join(parts[:3])  # Limit to 3 args for readability
