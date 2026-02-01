"""
Exception type identification module.

This module provides utilities for identifying and mapping Python exception types
to explanation templates. It supports the following exception types:
- TypeError
- ValueError
- IndexError
- KeyError
- AttributeError
- FileNotFoundError
- PermissionError
- ZeroDivisionError
- NameError
- And provides fallback for unknown exception types
"""

from typing import Dict, Type, Optional, Callable
from dataclasses import dataclass


@dataclass
class ExceptionTypeInfo:
    """Information about an exception type."""
    exception_class: Type[Exception]
    name: str
    description: str
    common_causes: list


# Mapping of exception types to their information and explanation templates
EXCEPTION_TYPE_MAPPING: Dict[Type[Exception], ExceptionTypeInfo] = {
    TypeError: ExceptionTypeInfo(
        exception_class=TypeError,
        name="TypeError",
        description="Type mismatch or incompatible operation",
        common_causes=[
            "Mixing incompatible types (e.g., adding string and number)",
            "Wrong number of function arguments",
            "Calling a non-callable object",
            "Invalid operation for the given type"
        ]
    ),
    ValueError: ExceptionTypeInfo(
        exception_class=ValueError,
        name="ValueError",
        description="Invalid value for the operation",
        common_causes=[
            "Invalid literal for type conversion",
            "Unpacking wrong number of values",
            "Invalid argument value",
            "String format error"
        ]
    ),
    IndexError: ExceptionTypeInfo(
        exception_class=IndexError,
        name="IndexError",
        description="Sequence index out of range",
        common_causes=[
            "Accessing list/string index that doesn't exist",
            "Index too large or negative",
            "Empty sequence access",
            "Off-by-one error in loop"
        ]
    ),
    KeyError: ExceptionTypeInfo(
        exception_class=KeyError,
        name="KeyError",
        description="Dictionary key not found",
        common_causes=[
            "Accessing non-existent dictionary key",
            "Typo in key name",
            "Key not added to dictionary",
            "Wrong key type"
        ]
    ),
    AttributeError: ExceptionTypeInfo(
        exception_class=AttributeError,
        name="AttributeError",
        description="Attribute or method not found on object",
        common_causes=[
            "Typo in attribute/method name",
            "Wrong object type",
            "Object not initialized",
            "Attribute doesn't exist on this type"
        ]
    ),
    FileNotFoundError: ExceptionTypeInfo(
        exception_class=FileNotFoundError,
        name="FileNotFoundError",
        description="File or directory not found",
        common_causes=[
            "File path is incorrect",
            "File doesn't exist",
            "Wrong working directory",
            "Typo in filename"
        ]
    ),
    PermissionError: ExceptionTypeInfo(
        exception_class=PermissionError,
        name="PermissionError",
        description="Permission denied for file operation",
        common_causes=[
            "Insufficient file permissions",
            "File is read-only",
            "Directory is protected",
            "Running without required privileges"
        ]
    ),
    ZeroDivisionError: ExceptionTypeInfo(
        exception_class=ZeroDivisionError,
        name="ZeroDivisionError",
        description="Division by zero",
        common_causes=[
            "Dividing by zero",
            "Modulo by zero",
            "Denominator is zero",
            "Variable contains zero unexpectedly"
        ]
    ),
    NameError: ExceptionTypeInfo(
        exception_class=NameError,
        name="NameError",
        description="Name not defined",
        common_causes=[
            "Variable not defined",
            "Typo in variable name",
            "Variable used before definition",
            "Variable out of scope"
        ]
    ),
}


def identify_exception_type(exception: Exception) -> str:
    """
    Identify the type of an exception and return its name.
    
    Args:
        exception: The exception object to identify
        
    Returns:
        String name of the exception type (e.g., "TypeError", "ValueError")
        
    Raises:
        TypeError: If the argument is not an Exception instance
        
    Example:
        >>> try:
        ...     x = 1 / 0
        ... except Exception as e:
        ...     exc_type = identify_exception_type(e)
        ...     print(exc_type)  # "ZeroDivisionError"
    """
    if not isinstance(exception, Exception):
        raise TypeError(f"Expected Exception instance, got {type(exception).__name__}")
    
    exception_class = type(exception)
    
    # Check if it's a known exception type
    if exception_class in EXCEPTION_TYPE_MAPPING:
        return EXCEPTION_TYPE_MAPPING[exception_class].name
    
    # Check if it's a subclass of a known exception type
    for known_type, info in EXCEPTION_TYPE_MAPPING.items():
        if isinstance(exception, known_type):
            return info.name
    
    # Fallback for unknown exception types
    return exception_class.__name__


def get_exception_type_info(exception: Exception) -> ExceptionTypeInfo:
    """
    Get detailed information about an exception type.
    
    Args:
        exception: The exception object
        
    Returns:
        ExceptionTypeInfo object with details about the exception type,
        or a generic info object for unknown types
        
    Raises:
        TypeError: If the argument is not an Exception instance
        
    Example:
        >>> try:
        ...     d = {}
        ...     value = d['missing_key']
        ... except Exception as e:
        ...     info = get_exception_type_info(e)
        ...     print(info.description)  # "Dictionary key not found"
    """
    if not isinstance(exception, Exception):
        raise TypeError(f"Expected Exception instance, got {type(exception).__name__}")
    
    exception_class = type(exception)
    
    # Check if it's a known exception type
    if exception_class in EXCEPTION_TYPE_MAPPING:
        return EXCEPTION_TYPE_MAPPING[exception_class]
    
    # Check if it's a subclass of a known exception type
    for known_type, info in EXCEPTION_TYPE_MAPPING.items():
        if isinstance(exception, known_type):
            return info
    
    # Fallback for unknown exception types
    return ExceptionTypeInfo(
        exception_class=exception_class,
        name=exception_class.__name__,
        description="An unexpected error occurred",
        common_causes=["Unknown cause - check the error message for details"]
    )


def is_supported_exception_type(exception: Exception) -> bool:
    """
    Check if an exception type is explicitly supported.
    
    Args:
        exception: The exception object to check
        
    Returns:
        True if the exception type is in the supported list, False otherwise
        
    Raises:
        TypeError: If the argument is not an Exception instance
        
    Example:
        >>> try:
        ...     x = 1 / 0
        ... except Exception as e:
        ...     if is_supported_exception_type(e):
        ...         print("This exception type is supported")
    """
    if not isinstance(exception, Exception):
        raise TypeError(f"Expected Exception instance, got {type(exception).__name__}")
    
    exception_class = type(exception)
    
    # Check if it's a known exception type
    if exception_class in EXCEPTION_TYPE_MAPPING:
        return True
    
    # Check if it's a subclass of a known exception type
    for known_type in EXCEPTION_TYPE_MAPPING.keys():
        if isinstance(exception, known_type):
            return True
    
    return False


def get_exception_type_mapping() -> Dict[Type[Exception], ExceptionTypeInfo]:
    """
    Get the complete exception type mapping.
    
    Returns:
        Dictionary mapping exception classes to their information
        
    Example:
        >>> mapping = get_exception_type_mapping()
        >>> for exc_class, info in mapping.items():
        ...     print(f"{info.name}: {info.description}")
    """
    return EXCEPTION_TYPE_MAPPING.copy()


def get_supported_exception_types() -> list:
    """
    Get a list of all supported exception types.
    
    Returns:
        List of supported exception type names
        
    Example:
        >>> types = get_supported_exception_types()
        >>> print(types)
        ['TypeError', 'ValueError', 'IndexError', ...]
    """
    return [info.name for info in EXCEPTION_TYPE_MAPPING.values()]
