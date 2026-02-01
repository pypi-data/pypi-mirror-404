"""
Custom exception classes for fishertools error handling.

This module defines the exception hierarchy for fishertools, providing
specific error types for different failure scenarios.
"""


class FishertoolsError(Exception):
    """
    Base exception class for all fishertools-specific errors.
    
    This is the parent class for all custom exceptions in fishertools.
    It provides a consistent interface and allows catching all fishertools
    errors with a single except clause.
    """
    
    def __init__(self, message: str, original_error: Exception = None):
        """
        Initialize the fishertools error.
        
        Args:
            message: Human-readable error message in Russian
            original_error: The original exception that caused this error (optional)
        """
        super().__init__(message)
        self.message = message
        self.original_error = original_error
    
    def __str__(self) -> str:
        """Return the error message."""
        return self.message
    
    def get_full_message(self) -> str:
        """
        Get the full error message including original error if available.
        
        Returns:
            Complete error message with context
        """
        if self.original_error:
            return f"{self.message} (Причина: {self.original_error})"
        return self.message


class ExplanationError(FishertoolsError):
    """
    Exception raised when error explanation fails.
    
    This exception is raised when the ErrorExplainer cannot create
    a proper explanation for a given exception, typically due to
    pattern matching failures or internal processing errors.
    """
    
    def __init__(self, message: str, exception_type: str = None, original_error: Exception = None):
        """
        Initialize the explanation error.
        
        Args:
            message: Description of what went wrong during explanation
            exception_type: The type of exception that couldn't be explained
            original_error: The original exception that caused this error
        """
        super().__init__(message, original_error)
        self.exception_type = exception_type
    
    def get_full_message(self) -> str:
        """Get the full error message with exception type context."""
        base_message = super().get_full_message()
        if self.exception_type:
            return f"{base_message} (Тип исключения: {self.exception_type})"
        return base_message


class FormattingError(FishertoolsError):
    """
    Exception raised when output formatting fails.
    
    This exception is raised when formatters cannot properly format
    an ErrorExplanation, typically due to invalid formatter configuration
    or output generation issues.
    """
    
    def __init__(self, message: str, formatter_type: str = None, original_error: Exception = None):
        """
        Initialize the formatting error.
        
        Args:
            message: Description of what went wrong during formatting
            formatter_type: The type of formatter that failed
            original_error: The original exception that caused this error
        """
        super().__init__(message, original_error)
        self.formatter_type = formatter_type
    
    def get_full_message(self) -> str:
        """Get the full error message with formatter type context."""
        base_message = super().get_full_message()
        if self.formatter_type:
            return f"{base_message} (Тип форматтера: {self.formatter_type})"
        return base_message


class ConfigurationError(FishertoolsError):
    """
    Exception raised when configuration is invalid.
    
    This exception is raised when ExplainerConfig or other configuration
    objects contain invalid values that prevent proper system operation.
    """
    
    def __init__(self, message: str, config_field: str = None, config_value: str = None, original_error: Exception = None):
        """
        Initialize the configuration error.
        
        Args:
            message: Description of the configuration problem
            config_field: The configuration field that has an invalid value
            config_value: The invalid value that caused the error
            original_error: The original exception that caused this error
        """
        super().__init__(message, original_error)
        self.config_field = config_field
        self.config_value = config_value
    
    def get_full_message(self) -> str:
        """Get the full error message with configuration context."""
        base_message = super().get_full_message()
        if self.config_field and self.config_value:
            return f"{base_message} (Поле: {self.config_field}, Значение: {self.config_value})"
        elif self.config_field:
            return f"{base_message} (Поле: {self.config_field})"
        return base_message


class PatternError(FishertoolsError):
    """
    Exception raised when error pattern operations fail.
    
    This exception is raised when ErrorPattern objects cannot be created,
    loaded, or used properly, typically due to invalid pattern definitions
    or pattern matching failures.
    """
    
    def __init__(self, message: str, pattern_type: str = None, original_error: Exception = None):
        """
        Initialize the pattern error.
        
        Args:
            message: Description of the pattern problem
            pattern_type: The type of pattern that caused the error
            original_error: The original exception that caused this error
        """
        super().__init__(message, original_error)
        self.pattern_type = pattern_type
    
    def get_full_message(self) -> str:
        """Get the full error message with pattern type context."""
        base_message = super().get_full_message()
        if self.pattern_type:
            return f"{base_message} (Тип паттерна: {self.pattern_type})"
        return base_message


class SafeUtilityError(FishertoolsError):
    """
    Exception raised when safe utility operations fail.
    
    This exception is raised when safe utility functions encounter
    errors that cannot be handled gracefully, typically due to
    invalid inputs or system-level failures.
    """
    
    def __init__(self, message: str, utility_name: str = None, original_error: Exception = None):
        """
        Initialize the safe utility error.
        
        Args:
            message: Description of the utility problem
            utility_name: The name of the utility function that failed
            original_error: The original exception that caused this error
        """
        super().__init__(message, original_error)
        self.utility_name = utility_name
    
    def get_full_message(self) -> str:
        """Get the full error message with utility name context."""
        base_message = super().get_full_message()
        if self.utility_name:
            return f"{base_message} (Утилита: {self.utility_name})"
        return base_message