"""
Safe input collection module for fishertools.

This module provides validated input collection functions with automatic type checking
and range validation. It helps beginners collect user input safely without writing
repetitive validation code.

Functions:
    ask_int() - Prompt user for an integer with optional range validation
    ask_float() - Prompt user for a float with optional range validation
    ask_str() - Prompt user for a string with optional length validation
    ask_choice() - Prompt user to choose from a list of options
"""

from typing import List, Optional, Any, Callable, Union, TypeVar

# Security constants
MAX_INPUT_LENGTH = 10000  # Maximum input length to prevent DoS
DEFAULT_TIMEOUT = 300  # 5 minutes default timeout

T = TypeVar('T', int, float)


def _ask_numeric(
    prompt: str,
    converter: Callable[[str], T],
    type_name: str,
    min_val: Optional[Union[int, float]] = None,
    max_val: Optional[Union[int, float]] = None,
    max_attempts: int = 10,
    timeout: Optional[int] = DEFAULT_TIMEOUT,
    max_input_length: int = MAX_INPUT_LENGTH
) -> T:
    """
    Internal function for numeric input with validation and security checks.
    
    Args:
        prompt: The prompt to display to the user
        converter: Function to convert string to numeric type (int or float)
        type_name: Name of the type for error messages
        min_val: Minimum allowed value (inclusive), optional
        max_val: Maximum allowed value (inclusive), optional
        max_attempts: Maximum number of attempts before raising error
        timeout: Timeout in seconds (None for no timeout)
        max_input_length: Maximum input length to prevent DoS
        
    Returns:
        Validated numeric value from user input
        
    Raises:
        ValueError: If validation fails or max attempts exceeded
        TimeoutError: If input timeout is exceeded
        EOFError: If user provides EOF (Ctrl+D)
        KeyboardInterrupt: If user cancels with Ctrl+C
    """
    import signal
    import sys
    
    # Валидация параметров
    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty")
    
    if min_val is not None and max_val is not None and min_val > max_val:
        raise ValueError(f"min_val ({min_val}) cannot be greater than max_val ({max_val})")
    
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")
    
    if max_input_length < 1:
        raise ValueError("max_input_length must be at least 1")
    
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Input timeout ({timeout}s) exceeded")
    
    # Set up timeout (only on Unix-like systems)
    old_handler = None
    if timeout is not None and hasattr(signal, 'SIGALRM'):
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)
    
    try:
        attempts = 0
        while attempts < max_attempts:
            attempts += 1
            try:
                user_input = input(prompt)
                
                # Security: Check input length to prevent DoS
                if len(user_input) > max_input_length:
                    remaining = max_attempts - attempts
                    print(f"Error: Input too long (max {max_input_length} characters). {remaining} attempts remaining.")
                    continue
                
                # Convert to numeric type
                value = converter(user_input)
                
                # Check min constraint
                if min_val is not None and value < min_val:
                    remaining = max_attempts - attempts
                    print(f"Error: Value must be at least {min_val}. {remaining} attempts remaining.")
                    continue
                
                # Check max constraint
                if max_val is not None and value > max_val:
                    remaining = max_attempts - attempts
                    print(f"Error: Value must be at most {max_val}. {remaining} attempts remaining.")
                    continue
                
                return value
                
            except ValueError:
                remaining = max_attempts - attempts
                print(f"Error: Please enter a valid {type_name}. {remaining} attempts remaining.")
            except (EOFError, KeyboardInterrupt):
                raise
        
        raise ValueError(f"Maximum attempts ({max_attempts}) exceeded")
    
    finally:
        # Clean up timeout
        if timeout is not None and hasattr(signal, 'SIGALRM'):
            signal.alarm(0)
            if old_handler is not None:
                signal.signal(signal.SIGALRM, old_handler)


def ask_int(
    prompt: str, 
    min_val: Optional[int] = None, 
    max_val: Optional[int] = None,
    max_attempts: int = 10,
    timeout: Optional[int] = DEFAULT_TIMEOUT
) -> int:
    """
    Prompt user for an integer with optional range validation.
    
    Security features:
    - Input length limit to prevent DoS attacks
    - Optional timeout to prevent infinite waiting
    - Maximum attempts limit
    
    Args:
        prompt: The prompt to display to the user
        min_val: Minimum allowed value (inclusive), optional
        max_val: Maximum allowed value (inclusive), optional
        max_attempts: Maximum number of attempts before raising error
        timeout: Timeout in seconds (None for no timeout, default: 300s)
        
    Returns:
        Validated integer from user input
        
    Raises:
        ValueError: If prompt is empty, min_val > max_val, or max attempts exceeded
        TimeoutError: If input timeout is exceeded
        EOFError: If user provides EOF (Ctrl+D)
        KeyboardInterrupt: If user cancels with Ctrl+C
        
    Example:
        >>> age = ask_int("How old are you? ", min_val=0, max_val=150)
        >>> score = ask_int("Enter your score: ", timeout=60)
    """
    return _ask_numeric(prompt, int, "integer", min_val, max_val, max_attempts, timeout)


def ask_float(
    prompt: str, 
    min_val: Optional[float] = None, 
    max_val: Optional[float] = None,
    max_attempts: int = 10,
    timeout: Optional[int] = DEFAULT_TIMEOUT
) -> float:
    """
    Prompt user for a float with optional range validation.
    
    Security features:
    - Input length limit to prevent DoS attacks
    - Optional timeout to prevent infinite waiting
    - Maximum attempts limit
    
    Args:
        prompt: The prompt to display to the user
        min_val: Minimum allowed value (inclusive), optional
        max_val: Maximum allowed value (inclusive), optional
        max_attempts: Maximum number of attempts before raising error
        timeout: Timeout in seconds (None for no timeout, default: 300s)
        
    Returns:
        Validated float from user input
        
    Raises:
        ValueError: If prompt is empty, min_val > max_val, or max attempts exceeded
        TimeoutError: If input timeout is exceeded
        EOFError: If user provides EOF (Ctrl+D)
        KeyboardInterrupt: If user cancels with Ctrl+C
        
    Example:
        >>> temperature = ask_float("Enter temperature (C): ", min_val=-273.15, timeout=60)
        >>> price = ask_float("Enter price: ", min_val=0)
    """
    return _ask_numeric(prompt, float, "number", min_val, max_val, max_attempts, timeout)


def ask_str(prompt: str, min_length: Optional[int] = None, max_length: Optional[int] = None) -> str:
    """
    Prompt user for a string with optional length validation.
    
    Args:
        prompt: The prompt to display to the user
        min_length: Minimum string length, optional
        max_length: Maximum string length, optional
        
    Returns:
        Validated string from user input (whitespace stripped)
        
    Raises:
        EOFError: If user provides EOF (Ctrl+D)
        
    Example:
        >>> name = ask_str("Enter your name: ", min_length=1, max_length=50)
        >>> password = ask_str("Enter password: ", min_length=8)
    """
    while True:
        try:
            user_input = input(prompt)
            value = user_input.strip()
            
            # Check min_length constraint
            if min_length is not None and len(value) < min_length:
                print(f"Error: String must be at least {min_length} characters long")
                continue
            
            # Check max_length constraint
            if max_length is not None and len(value) > max_length:
                print(f"Error: String must be at most {max_length} characters long")
                continue
            
            return value
        except EOFError:
            raise


def ask_choice(prompt: str, options: List[str]) -> str:
    """
    Prompt user to choose from a list of options.
    
    Args:
        prompt: The prompt to display to the user
        options: List of available choices
        
    Returns:
        The selected option (exact string from options list)
        
    Raises:
        EOFError: If user provides EOF (Ctrl+D)
        ValueError: If options list is empty
        
    Example:
        >>> color = ask_choice("Choose a color: ", ["red", "green", "blue"])
        >>> choice = ask_choice("Select: ", ["Yes", "No", "Maybe"])
    """
    if not options:
        raise ValueError("Options list cannot be empty")
    
    while True:
        try:
            # Display options
            for i, option in enumerate(options, 1):
                print(f"  {i}. {option}")
            
            user_input = input(prompt).strip()
            
            # Try numeric selection first
            try:
                choice_index = int(user_input) - 1
                if 0 <= choice_index < len(options):
                    return options[choice_index]
                else:
                    print(f"Error: Please enter a number between 1 and {len(options)}")
                    continue
            except ValueError:
                # Try direct text matching
                if user_input in options:
                    return user_input
                else:
                    print(f"Error: '{user_input}' is not a valid option")
                    continue
        except EOFError:
            raise
