"""
Deprecation warning system for fishertools

This module provides utilities for managing deprecation warnings and 
migration guidance for functions being removed from the library.
"""

import warnings
import functools
from typing import Callable, Optional


def deprecated(
    reason: str = "This function is deprecated",
    alternative: Optional[str] = None,
    removal_version: Optional[str] = None
) -> Callable:
    """
    Decorator to mark functions as deprecated with clear migration guidance.
    
    Args:
        reason: Explanation of why the function is deprecated
        alternative: Suggested replacement function or approach
        removal_version: Version when the function will be removed
    
    Returns:
        Decorated function that issues deprecation warning when called
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Build comprehensive warning message
            message_parts = [
                f"Функция '{func.__name__}' устарела.",
                reason
            ]
            
            if alternative:
                message_parts.append(f"Используйте вместо неё: {alternative}")
            
            if removal_version:
                message_parts.append(f"Будет удалена в версии {removal_version}")
            
            message_parts.append("Подробности миграции: https://github.com/f1sherFM/fishertools/wiki/migration")
            
            warning_message = " ".join(message_parts)
            
            # Issue deprecation warning
            warnings.warn(
                warning_message,
                DeprecationWarning,
                stacklevel=2
            )
            
            # Execute original function
            return func(*args, **kwargs)
        
        # Mark function as deprecated for introspection
        wrapper._is_deprecated = True
        wrapper._deprecation_info = {
            'reason': reason,
            'alternative': alternative,
            'removal_version': removal_version
        }
        
        return wrapper
    return decorator


def show_deprecation_info(func: Callable) -> dict:
    """
    Get deprecation information for a function.
    
    Args:
        func: Function to check for deprecation info
        
    Returns:
        Dictionary with deprecation details or empty dict if not deprecated
    """
    if hasattr(func, '_is_deprecated') and func._is_deprecated:
        return func._deprecation_info.copy()
    return {}


def list_deprecated_functions(module) -> list:
    """
    List all deprecated functions in a module.
    
    Args:
        module: Module to scan for deprecated functions
        
    Returns:
        List of deprecated function names
    """
    deprecated_funcs = []
    
    for name in dir(module):
        obj = getattr(module, name)
        if callable(obj) and hasattr(obj, '_is_deprecated') and obj._is_deprecated:
            deprecated_funcs.append(name)
    
    return deprecated_funcs


# Example deprecated functions for demonstration
@deprecated(
    reason="Эта функция не соответствует новой миссии библиотеки",
    alternative="fishertools.safe.safe_read_file()",
    removal_version="1.0.0"
)
def unsafe_file_reader(filepath: str) -> str:
    """
    DEPRECATED: Небезопасное чтение файла без обработки ошибок
    
    Эта функция устарела и будет удалена в версии 1.0.0.
    Используйте вместо неё fishertools.safe.safe_read_file()
    """
    with open(filepath, 'r') as f:
        return f.read()


@deprecated(
    reason="Функция может вызывать ошибки у новичков",
    alternative="fishertools.safe.safe_divide()",
    removal_version="1.0.0"
)
def risky_divide(a: float, b: float) -> float:
    """
    DEPRECATED: Деление без проверки на ноль
    
    Эта функция устарела и будет удалена в версии 1.0.0.
    Используйте вместо неё fishertools.safe.safe_divide()
    """
    return a / b


@deprecated(
    reason="Слишком сложная для новичков",
    alternative="Используйте стандартные методы списков",
    removal_version="1.0.0"
)
def complex_list_operation(lst: list) -> list:
    """
    DEPRECATED: Сложная операция со списком
    
    Эта функция устарела и будет удалена в версии 1.0.0.
    Используйте стандартные методы списков для простоты.
    """
    return [x for i, x in enumerate(lst) if i % 2 == 0 and x is not None]