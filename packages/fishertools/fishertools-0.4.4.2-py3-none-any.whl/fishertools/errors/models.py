"""
Core data models for the error explanation system.
"""

from dataclasses import dataclass, asdict
from typing import List, Optional, Any, Dict
import json


@dataclass
class ErrorPattern:
    """
    Model for error explanation patterns.
    
    Defines how to match and explain specific types of Python exceptions.
    """
    error_type: type
    error_keywords: List[str]  # Keywords in error message to match
    explanation: str           # Simple explanation in Russian
    tip: str                  # Advice on how to fix
    example: str              # Code example
    common_causes: List[str]  # Common causes of this error
    
    def __post_init__(self):
        """Validate the pattern after initialization."""
        from .exceptions import PatternError
        
        # Allow empty keywords for patterns that match any exception of a type (like KeyError)
        if not self.error_keywords and not (len(self.error_keywords) == 1 and self.error_keywords[0] == ""):
            raise PatternError("error_keywords cannot be empty unless it contains a single empty string")
        if not self.explanation.strip():
            raise PatternError("explanation cannot be empty")
        if not self.tip.strip():
            raise PatternError("tip cannot be empty")
        if not self.example.strip():
            raise PatternError("example cannot be empty")
    
    def matches(self, exception: Exception) -> bool:
        """
        Check if this pattern matches the given exception.
        
        Args:
            exception: The exception to check
            
        Returns:
            True if pattern matches, False otherwise
        """
        if not isinstance(exception, self.error_type):
            return False
        
        # If no keywords specified, match any exception of this type
        if not self.error_keywords or (len(self.error_keywords) == 1 and self.error_keywords[0] == ""):
            return True
        
        error_message = str(exception).lower()
        return any(keyword.lower() in error_message for keyword in self.error_keywords)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert pattern to dictionary for serialization.
        
        Returns:
            Dictionary representation of the pattern
        """
        result = asdict(self)
        # Convert type to string for JSON serialization
        result['error_type'] = self.error_type.__name__
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ErrorPattern':
        """
        Create ErrorPattern from dictionary.
        
        Args:
            data: Dictionary containing pattern data
            
        Returns:
            ErrorPattern instance
        """
        from .exceptions import PatternError
        
        try:
            # Convert string back to type
            error_type_name = data.pop('error_type')
            error_type = getattr(__builtins__, error_type_name, Exception)
            return cls(error_type=error_type, **data)
        except Exception as e:
            raise PatternError(f"Не удалось создать ErrorPattern из словаря: {e}", original_error=e)


@dataclass
class ErrorExplanation:
    """
    Model for structured error explanations.
    
    Contains all information needed to present a helpful error explanation.
    """
    original_error: str
    error_type: str
    simple_explanation: str
    fix_tip: str
    code_example: str
    additional_info: Optional[str] = None
    
    def __post_init__(self):
        """Validate the explanation after initialization."""
        from .exceptions import ExplanationError
        
        # Allow empty or whitespace-only original_error since exceptions can have empty messages
        if self.original_error is None:
            raise ExplanationError("original_error cannot be None")
        if not self.simple_explanation.strip():
            raise ExplanationError("simple_explanation cannot be empty")
        if not self.fix_tip.strip():
            raise ExplanationError("fix_tip cannot be empty")
        if not self.code_example.strip():
            raise ExplanationError("code_example cannot be empty")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert explanation to dictionary for serialization.
        
        Returns:
            Dictionary representation of the explanation
        """
        return asdict(self)
    
    def to_json(self) -> str:
        """
        Convert explanation to JSON string.
        
        Returns:
            JSON representation of the explanation
        """
        try:
            return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
        except Exception as e:
            from .exceptions import FormattingError
            raise FormattingError(f"Не удалось преобразовать объяснение в JSON: {e}", 
                                formatter_type="json", original_error=e)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ErrorExplanation':
        """
        Create ErrorExplanation from dictionary.
        
        Args:
            data: Dictionary containing explanation data
            
        Returns:
            ErrorExplanation instance
        """
        try:
            return cls(**data)
        except Exception as e:
            from .exceptions import ExplanationError
            raise ExplanationError(f"Не удалось создать ErrorExplanation из словаря: {e}", original_error=e)


@dataclass
class ExplainerConfig:
    """
    Configuration for the error explanation system.
    
    Controls how errors are explained and formatted.
    """
    language: str = 'ru'
    format_type: str = 'console'
    show_original_error: bool = True
    show_traceback: bool = False
    use_colors: bool = True
    max_explanation_length: int = 200
    
    def __post_init__(self):
        """Validate the configuration after initialization."""
        from .exceptions import ConfigurationError
        
        if self.language not in ['ru', 'en']:
            raise ConfigurationError("language must be 'ru' or 'en'", 
                                   config_field="language", config_value=self.language)
        if self.format_type not in ['console', 'json', 'plain']:
            raise ConfigurationError("format_type must be 'console', 'json', or 'plain'", 
                                   config_field="format_type", config_value=self.format_type)
        if self.max_explanation_length <= 0:
            raise ConfigurationError("max_explanation_length must be positive", 
                                   config_field="max_explanation_length", 
                                   config_value=str(self.max_explanation_length))
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Returns:
            Dictionary representation of the configuration
        """
        return asdict(self)
    
    def to_json(self) -> str:
        """
        Convert configuration to JSON string.
        
        Returns:
            JSON representation of the configuration
        """
        try:
            return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
        except Exception as e:
            from .exceptions import FormattingError
            raise FormattingError(f"Не удалось преобразовать конфигурацию в JSON: {e}", 
                                formatter_type="json", original_error=e)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExplainerConfig':
        """
        Create ExplainerConfig from dictionary.
        
        Args:
            data: Dictionary containing configuration data
            
        Returns:
            ExplainerConfig instance
        """
        try:
            return cls(**data)
        except Exception as e:
            from .exceptions import ConfigurationError
            raise ConfigurationError(f"Не удалось создать ExplainerConfig из словаря: {e}", original_error=e)



@dataclass
class ExceptionExplanation:
    """
    Structured explanation of an exception.
    
    This dataclass provides a comprehensive explanation of a Python exception,
    including the exception type, a simple explanation, fix suggestions,
    a code example, and optional traceback context.
    """
    exception_type: str
    simple_explanation: str
    fix_suggestions: List[str]
    code_example: str
    traceback_context: Optional[str] = None
    
    def __post_init__(self):
        """Validate the explanation after initialization."""
        from .exceptions import ExplanationError
        
        if not self.exception_type.strip():
            raise ExplanationError("exception_type cannot be empty")
        if not self.simple_explanation.strip():
            raise ExplanationError("simple_explanation cannot be empty")
        if not self.fix_suggestions:
            raise ExplanationError("fix_suggestions cannot be empty")
        if not all(isinstance(s, str) and s.strip() for s in self.fix_suggestions):
            raise ExplanationError("All fix_suggestions must be non-empty strings")
        if not self.code_example.strip():
            raise ExplanationError("code_example cannot be empty")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert explanation to dictionary for serialization.
        
        Returns:
            Dictionary representation of the explanation
        """
        return asdict(self)
    
    def to_json(self) -> str:
        """
        Convert explanation to JSON string.
        
        Returns:
            JSON representation of the explanation
        """
        try:
            return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
        except Exception as e:
            from .exceptions import FormattingError
            raise FormattingError(f"Could not convert explanation to JSON: {e}", 
                                formatter_type="json", original_error=e)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExceptionExplanation':
        """
        Create ExceptionExplanation from dictionary.
        
        Args:
            data: Dictionary containing explanation data
            
        Returns:
            ExceptionExplanation instance
        """
        try:
            return cls(**data)
        except Exception as e:
            from .exceptions import ExplanationError
            raise ExplanationError(f"Could not create ExceptionExplanation from dictionary: {e}", original_error=e)
