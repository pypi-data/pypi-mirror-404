"""
Legacy module for backward compatibility

This module contains functions from the original fishertools library that align
with the new mission of making Python more convenient and safer for beginners.
All functions maintain identical behavior for backward compatibility.

It also includes deprecated functions with clear migration guidance.
"""

# Import deprecation system
from .deprecation import (
    deprecated,
    show_deprecation_info,
    list_deprecated_functions,
    # Example deprecated functions for demonstration
    unsafe_file_reader,
    risky_divide,
    complex_list_operation,
)

# Import retained functions that align with beginner-friendly mission
from .deprecated import (
    # File and directory utilities - helpful for beginners
    read_json,
    write_json, 
    ensure_dir,
    get_file_size,
    list_files,
    
    # String utilities - common beginner needs
    clean_string,
    validate_email,
    
    # Data utilities - safe operations for beginners
    chunk_list,
    merge_dicts,
    flatten_dict,
    
    # Configuration helper - simplified config management
    QuickConfig,
    
    # Simple logging - educational and beginner-friendly
    SimpleLogger,
    
    # Decorators that help beginners understand code behavior
    timer,
    debug,
    retry,
    cache_result,
    validate_types,
    
    # Utility functions
    timestamp,
    generate_password,
    hash_string,
)

__all__ = [
    # Deprecation system
    'deprecated', 'show_deprecation_info', 'list_deprecated_functions',
    # Example deprecated functions
    'unsafe_file_reader', 'risky_divide', 'complex_list_operation',
    # File operations
    'read_json', 'write_json', 'ensure_dir', 'get_file_size', 'list_files',
    # String operations  
    'clean_string', 'validate_email',
    # Data operations
    'chunk_list', 'merge_dicts', 'flatten_dict',
    # Helper classes
    'QuickConfig', 'SimpleLogger', 
    # Decorators
    'timer', 'debug', 'retry', 'cache_result', 'validate_types',
    # Utilities
    'timestamp', 'generate_password', 'hash_string',
]