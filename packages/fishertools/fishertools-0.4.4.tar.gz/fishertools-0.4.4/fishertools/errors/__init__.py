"""
Error explanation system for fishertools.

This module provides tools to explain Python errors in simple, understandable terms
for beginners learning Python.
"""

from .explainer import ErrorExplainer, explain_error
from .patterns import ErrorPattern
from .formatters import ConsoleFormatter, PlainFormatter, JsonFormatter, get_formatter
from .models import ErrorExplanation, ExplainerConfig, ExceptionExplanation
from .exceptions import (
    FishertoolsError, ExplanationError, FormattingError, 
    ConfigurationError, PatternError, SafeUtilityError
)
from .recovery import (
    ErrorRecoveryManager, ErrorSeverity, RecoveryStrategy, ErrorContext, RecoveryAction,
    get_recovery_manager, handle_error_with_recovery, with_error_recovery
)
from .exception_types import (
    identify_exception_type, get_exception_type_info, is_supported_exception_type,
    get_exception_type_mapping, get_supported_exception_types, ExceptionTypeInfo,
    EXCEPTION_TYPE_MAPPING
)

__all__ = [
    "ErrorExplainer", "explain_error", "ErrorPattern", 
    "ConsoleFormatter", "PlainFormatter", "JsonFormatter", "get_formatter",
    "ErrorExplanation", "ExceptionExplanation", "ExplainerConfig",
    "FishertoolsError", "ExplanationError", "FormattingError", 
    "ConfigurationError", "PatternError", "SafeUtilityError",
    "ErrorRecoveryManager", "ErrorSeverity", "RecoveryStrategy", "ErrorContext", "RecoveryAction",
    "get_recovery_manager", "handle_error_with_recovery", "with_error_recovery",
    "identify_exception_type", "get_exception_type_info", "is_supported_exception_type",
    "get_exception_type_mapping", "get_supported_exception_types", "ExceptionTypeInfo",
    "EXCEPTION_TYPE_MAPPING"
]