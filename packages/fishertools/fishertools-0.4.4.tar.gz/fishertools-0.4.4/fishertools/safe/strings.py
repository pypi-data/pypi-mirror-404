"""
Safe string operations for beginners.

This module provides safe string handling utilities that gracefully
handle None values and common string operation errors.
"""

from typing import Optional, List, Any


def safe_strip(text: Optional[str], chars: Optional[str] = None, default: str = '') -> str:
    """
    Safely strip whitespace or characters from a string.
    
    Handles None values gracefully instead of raising AttributeError.
    
    Args:
        text: String to strip (can be None)
        chars: Characters to remove (None means whitespace)
        default: Value to return if text is None
        
    Returns:
        Stripped string or default value
        
    Examples:
        >>> safe_strip("  hello  ")
        'hello'
        >>> safe_strip(None)
        ''
        >>> safe_strip(None, default="N/A")
        'N/A'
        >>> safe_strip("...hello...", chars=".")
        'hello'
    """
    if text is None:
        return default
    try:
        return text.strip(chars)
    except (AttributeError, TypeError):
        return default


def safe_split(text: Optional[str], sep: Optional[str] = None, 
               maxsplit: int = -1, default: Optional[List[str]] = None) -> List[str]:
    """
    Safely split a string into a list.
    
    Handles None values and returns empty list or default instead of raising errors.
    
    Args:
        text: String to split (can be None)
        sep: Separator (None means any whitespace)
        maxsplit: Maximum number of splits
        default: Value to return if text is None (defaults to empty list)
        
    Returns:
        List of strings or default value
        
    Examples:
        >>> safe_split("a,b,c", ",")
        ['a', 'b', 'c']
        >>> safe_split(None)
        []
        >>> safe_split(None, default=["N/A"])
        ['N/A']
        >>> safe_split("a b c", maxsplit=1)
        ['a', 'b c']
    """
    if default is None:
        default = []
    
    if text is None:
        return default
    
    try:
        return text.split(sep, maxsplit)
    except (AttributeError, TypeError):
        return default


def safe_join(separator: str, items: List[Any], skip_none: bool = True, 
              stringify: bool = True) -> str:
    """
    Safely join items into a string.
    
    Handles None values in the list and can convert non-strings to strings.
    
    Args:
        separator: String to use between items
        items: List of items to join (can contain None)
        skip_none: If True, skip None values; if False, convert to "None"
        stringify: If True, convert non-strings to strings
        
    Returns:
        Joined string
        
    Examples:
        >>> safe_join(", ", ["a", "b", "c"])
        'a, b, c'
        >>> safe_join(", ", ["a", None, "c"])
        'a, c'
        >>> safe_join(", ", ["a", None, "c"], skip_none=False)
        'a, None, c'
        >>> safe_join("-", [1, 2, 3])
        '1-2-3'
    """
    if items is None:
        return ""
    
    try:
        processed = []
        for item in items:
            if item is None:
                if not skip_none:
                    processed.append("None")
            elif stringify and not isinstance(item, str):
                processed.append(str(item))
            else:
                processed.append(item)
        
        return separator.join(processed)
    except (TypeError, AttributeError):
        return ""


def safe_format(template: str, *args, **kwargs) -> str:
    """
    Safely format a string template.
    
    Returns the original template if formatting fails instead of raising errors.
    
    Args:
        template: Format string template
        *args: Positional arguments for formatting
        **kwargs: Keyword arguments for formatting
        
    Returns:
        Formatted string or original template if formatting fails
        
    Examples:
        >>> safe_format("Hello, {}!", "World")
        'Hello, World!'
        >>> safe_format("Hello, {name}!", name="Alice")
        'Hello, Alice!'
        >>> safe_format("Hello, {}!")  # Missing argument
        'Hello, {}!'
        >>> safe_format("Value: {:.2f}", 3.14159)
        'Value: 3.14'
    """
    try:
        return template.format(*args, **kwargs)
    except (KeyError, IndexError, ValueError, TypeError):
        return template


def safe_lower(text: Optional[str], default: str = '') -> str:
    """
    Safely convert string to lowercase.
    
    Args:
        text: String to convert (can be None)
        default: Value to return if text is None
        
    Returns:
        Lowercase string or default value
        
    Examples:
        >>> safe_lower("HELLO")
        'hello'
        >>> safe_lower(None)
        ''
    """
    if text is None:
        return default
    try:
        return text.lower()
    except (AttributeError, TypeError):
        return default


def safe_upper(text: Optional[str], default: str = '') -> str:
    """
    Safely convert string to uppercase.
    
    Args:
        text: String to convert (can be None)
        default: Value to return if text is None
        
    Returns:
        Uppercase string or default value
        
    Examples:
        >>> safe_upper("hello")
        'HELLO'
        >>> safe_upper(None)
        ''
    """
    if text is None:
        return default
    try:
        return text.upper()
    except (AttributeError, TypeError):
        return default


__all__ = [
    'safe_strip',
    'safe_split', 
    'safe_join',
    'safe_format',
    'safe_lower',
    'safe_upper'
]