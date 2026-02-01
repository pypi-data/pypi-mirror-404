"""
Safe collection operations for beginners.

This module provides safe versions of common collection operations
that prevent typical mistakes and provide helpful error messages.
"""

from typing import Any, Optional, Union, List, Dict, Tuple


def safe_get(collection: Union[List, Tuple, Dict, str], 
             index: Union[int, str], 
             default: Any = None) -> Any:
    """
    Safely get an element from a collection by index or key.
    
    Works with lists, tuples, dicts, and strings. Returns default value
    instead of raising KeyError or IndexError.
    
    Args:
        collection: Collection (list, tuple, dict, or string)
        index: Index (for sequences) or key (for dicts)
        default: Value to return if element not found
        
    Returns:
        Element from collection or default value
        
    Raises:
        SafeUtilityError: If collection is None or obviously wrong type
        
    Examples:
        >>> safe_get([1, 2, 3], 1)
        2
        >>> safe_get([1, 2, 3], 10, "not found")
        'not found'
        >>> safe_get({"name": "Ivan"}, "name")
        'Ivan'
        >>> safe_get({"name": "Ivan"}, "age", 0)
        0
        >>> safe_get("hello", 0)
        'h'
        >>> safe_get("hello", 10)
        None
        
    Note:
        We check for obviously wrong types (None, bool, numbers) to help beginners.
        For valid collection types, we use EAFP (Easier to Ask Forgiveness than Permission).
    """
    from ..errors.exceptions import SafeUtilityError
    
    # Check for obviously wrong types that beginners might pass
    if collection is None or isinstance(collection, (bool, int, float, complex)):
        raise SafeUtilityError(
            "Коллекция не может быть None или числом. Передайте список, кортеж, словарь или строку.",
            utility_name="safe_get"
        )
    
    # For everything else, use EAFP - try and handle exceptions
    try:
        return collection[index]
    except (KeyError, IndexError, TypeError):
        # KeyError: dict key not found
        # IndexError: sequence index out of range
        # TypeError: wrong index type or unsupported collection
        return default


def safe_divide(a: Union[int, float], b: Union[int, float], 
                default: Optional[Union[int, float]] = None) -> Optional[Union[int, float]]:
    """
    Safely divide two numbers with zero division handling.
    
    Returns None when dividing by zero (mathematically correct: undefined).
    You can specify a custom default value if needed.
    
    Args:
        a: Dividend (number)
        b: Divisor (number)
        default: Value to return when dividing by zero (default: None)
        
    Returns:
        Result of division, or default value if b is zero
        
    Raises:
        SafeUtilityError: If arguments are obviously wrong types (None, bool, complex, str)
        
    Examples:
        >>> safe_divide(10, 2)
        5.0
        >>> safe_divide(10, 0)  # Mathematically undefined
        None
        >>> safe_divide(10, 0, default=0)  # Explicitly specified
        0
        >>> safe_divide(10, 0, default=float('inf'))
        inf
        
    Note:
        Division by zero is mathematically undefined. Returning 0 by default
        would be incorrect. Use default parameter if you need specific behavior.
    """
    from ..errors.exceptions import SafeUtilityError
    import math
    
    # Check for obviously wrong types that beginners might pass
    if a is None or isinstance(a, (bool, complex, str)):
        raise SafeUtilityError(
            f"Делимое должно быть числом (int или float), получен {type(a).__name__}",
            utility_name="safe_divide"
        )
    
    if b is None or isinstance(b, (bool, complex, str)):
        raise SafeUtilityError(
            f"Делитель должен быть числом (int или float), получен {type(b).__name__}",
            utility_name="safe_divide"
        )
    
    # Check for zero division
    if b == 0:
        return default
    
    try:
        # Perform division
        result = a / b
        
        # Check for infinity or NaN (edge cases)
        if math.isinf(result) or math.isnan(result):
            return default
        
        return result
    except (TypeError, ValueError):
        # Fallback for any other edge cases
        return default


def safe_max(collection: Union[List, Tuple], default: Any = None) -> Any:
    """
    Safely find maximum value in a collection.
    
    Returns default value for empty collections instead of raising ValueError.
    
    Args:
        collection: Collection of comparable items
        default: Value to return for empty collection
        
    Returns:
        Maximum value or default value
        
    Examples:
        >>> safe_max([1, 5, 3])
        5
        >>> safe_max([])
        None
        >>> safe_max([], 0)
        0
        >>> safe_max(['a', 'z', 'b'])
        'z'
    """
    try:
        return max(collection)
    except (ValueError, TypeError):
        # ValueError: empty sequence
        # TypeError: items not comparable
        return default


def safe_min(collection: Union[List, Tuple], default: Any = None) -> Any:
    """
    Safely find minimum value in a collection.
    
    Returns default value for empty collections instead of raising ValueError.
    
    Args:
        collection: Collection of comparable items
        default: Value to return for empty collection
        
    Returns:
        Minimum value or default value
        
    Examples:
        >>> safe_min([1, 5, 3])
        1
        >>> safe_min([])
        None
        >>> safe_min([], 0)
        0
        >>> safe_min(['a', 'z', 'b'])
        'a'
    """
    try:
        return min(collection)
    except (ValueError, TypeError):
        # ValueError: empty sequence
        # TypeError: items not comparable
        return default


def safe_sum(collection: Union[List, Tuple], default: Union[int, float] = 0) -> Union[int, float]:
    """
    Safely calculate sum of a collection.
    
    Returns default value for empty collections or if items can't be summed.
    
    Args:
        collection: Collection of numbers
        default: Value to return for empty collection or on error
        
    Returns:
        Sum of elements or default value
        
    Examples:
        >>> safe_sum([1, 2, 3])
        6
        >>> safe_sum([])
        0
        >>> safe_sum([], 10)
        10
        >>> safe_sum([1.5, 2.5, 3.0])
        7.0
    """
    # Handle empty collection explicitly
    if not collection:
        return default
    
    try:
        return sum(collection)
    except (TypeError, ValueError):
        # TypeError: items not numbers
        # ValueError: other calculation errors
        return default