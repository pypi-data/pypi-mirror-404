"""
Fishertools - инструменты, которые делают Python удобнее и безопаснее для новичков

Основная функция:
    explain_error() - объясняет ошибки Python в понятных словах

Модули:
    errors - система объяснения ошибок
    safe - безопасные утилиты для новичков
    learn - обучающие инструменты
    legacy - функции для обратной совместимости
"""

from ._version import __version__

__author__ = "f1sherFM"

# Primary API - main interface for users
from .errors import explain_error

# Exception classes for error handling
from .errors import (
    FishertoolsError, ExceptionExplanation, ExplanationError, FormattingError, 
    ConfigurationError, PatternError, SafeUtilityError
)

# Safe utilities - commonly used beginner-friendly functions
from .safe import (
    safe_get, safe_divide, safe_max, safe_min, safe_sum,
    safe_read_file, safe_write_file, safe_file_exists, 
    safe_get_file_size, safe_list_files,
    safe_open, find_file, project_root
)

# Learning tools - educational functions
from .learn import (
    generate_example, show_best_practice, 
    list_available_concepts, list_available_topics
)

# Input validation functions
from .input_utils import (
    ask_int, ask_float, ask_str, ask_choice
)

# Legacy imports for backward compatibility
from . import utils
from . import decorators  
from . import helpers

# Module imports for advanced users who want to access specific modules
from . import errors
from . import safe
from . import learn
from . import legacy
from . import input_utils

# New enhancement modules (fishertools-enhancements)
from . import learning
from . import documentation
from . import examples
from . import config
from . import integration

# Phase 1 modules (v0.5.0+)
from . import visualization
from . import validation
from . import debug

__all__ = [
    # Primary API - the main function users should import
    "explain_error",
    
    # Exception classes for error handling
    "FishertoolsError", "ExceptionExplanation", "ExplanationError", "FormattingError", 
    "ConfigurationError", "PatternError", "SafeUtilityError",
    
    # Safe utilities - direct access to commonly used functions
    "safe_get", "safe_divide", "safe_max", "safe_min", "safe_sum",
    "safe_read_file", "safe_write_file", "safe_file_exists", 
    "safe_get_file_size", "safe_list_files",
    "safe_open", "find_file", "project_root",
    
    # Input validation functions
    "ask_int", "ask_float", "ask_str", "ask_choice",
    
    # Learning tools - direct access to educational functions
    "generate_example", "show_best_practice", 
    "list_available_concepts", "list_available_topics",
    
    # Legacy modules for backward compatibility
    "utils", "decorators", "helpers",
    
    # New modules for advanced usage
    "errors", "safe", "learn", "legacy", "input_utils",
    
    # Enhancement modules (fishertools-enhancements)
    "learning", "documentation", "examples", "config", "integration",
    
    # Phase 1 modules (v0.4.1+)
    "visualization", "validation", "debug"
]