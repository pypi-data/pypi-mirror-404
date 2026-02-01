"""
Main error explainer implementation.

This module contains the ErrorExplainer class and explain_error function.

Architecture improvements (v0.4.4.2):
- Separated pattern loading into PatternLoader
- Separated pattern matching into PatternMatcher
- Separated explanation building into ExplanationBuilder
- Improved Single Responsibility Principle compliance
"""

from typing import Optional
from .models import ErrorExplanation, ExplainerConfig, ExceptionExplanation
from .pattern_loader import PatternLoader, PatternMatcher
from .explanation_builder import ExplanationBuilder
from .exceptions import ExplanationError, FormattingError, ConfigurationError, FishertoolsError


class ErrorExplainer:
    """
    Main class for explaining Python errors in simple terms.
    
    Uses pattern matching to provide contextual explanations for different
    types of Python exceptions.
    
    Architecture:
    - PatternLoader: Handles pattern loading and caching
    - PatternMatcher: Handles pattern matching logic
    - ExplanationBuilder: Handles explanation creation
    """
    
    def __init__(self, config: Optional[ExplainerConfig] = None):
        """
        Initialize the error explainer with optional configuration.
        
        Args:
            config: Configuration for the explainer behavior
            
        Raises:
            ConfigurationError: If the provided configuration is invalid
            ExplanationError: If pattern loading fails
        """
        try:
            self.config = config or ExplainerConfig()
            
            # Initialize components (SRP - Single Responsibility Principle)
            self.pattern_loader = PatternLoader()
            patterns = self.pattern_loader.load_patterns()
            self.pattern_matcher = PatternMatcher(patterns)
            self.explanation_builder = ExplanationBuilder()
            
        except Exception as e:
            if isinstance(e, (ConfigurationError, ExplanationError)):
                raise
            raise ExplanationError(
                f"Не удалось инициализировать ErrorExplainer: {e}",
                original_error=e
            )
    
    def explain(self, exception: Exception) -> ErrorExplanation:
        """
        Create an explanation for the given exception.
        
        Args:
            exception: The exception to explain
            
        Returns:
            Structured explanation of the error
            
        Raises:
            ExplanationError: If explanation creation fails
        """
        if not isinstance(exception, Exception):
            raise ExplanationError(
                f"Параметр должен быть экземпляром Exception, получен {type(exception).__name__}"
            )
        
        try:
            # Try to find a matching pattern
            pattern = self.pattern_matcher.find_match(exception)
            
            if pattern:
                return self.explanation_builder.create_from_pattern(exception, pattern)
            else:
                return self.explanation_builder.create_fallback(exception)
                
        except Exception as e:
            if isinstance(e, ExplanationError):
                raise
            # Graceful degradation
            return self.explanation_builder.create_emergency(exception, e)
    
    def explain_structured(self, exception: Exception) -> ExceptionExplanation:
        """
        Create a structured explanation for the given exception.
        
        This method generates an ExceptionExplanation object with all required fields:
        - exception_type: The type of the exception
        - simple_explanation: Plain-language explanation of what went wrong
        - fix_suggestions: List of ways to fix the problem
        - code_example: Minimal code example showing correct usage
        - traceback_context: Optional traceback information
        
        Args:
            exception: The exception to explain
            
        Returns:
            ExceptionExplanation object with structured explanation
            
        Raises:
            ExceptionError: If explanation creation fails
            
        Example:
            >>> try:
            ...     x = 1 / 0
            ... except Exception as e:
            ...     explanation = explainer.explain_structured(e)
            ...     print(explanation.simple_explanation)
        """
        if not isinstance(exception, Exception):
            raise ExplanationError(
                f"Параметр должен быть экземпляром Exception, получен {type(exception).__name__}"
            )
        
        try:
            # Get the basic explanation
            error_explanation = self.explain(exception)
            
            # Convert to structured format
            return self.explanation_builder.create_structured_from_basic(error_explanation)
            
        except Exception as e:
            if isinstance(e, ExplanationError):
                raise
            # Graceful degradation
            return self.explanation_builder.create_emergency_structured(exception, e)


def explain_error(exception: Exception, 
                 language: str = 'ru',
                 format_type: str = 'console',
                 **kwargs) -> None:
    """
    Main public API function for explaining Python errors in simple terms.
    
    This function takes any Python exception and provides a beginner-friendly
    explanation in Russian, including what the error means, how to fix it,
    and a relevant code example.
    
    Args:
        exception: The Python exception to explain (required)
        language: Language for explanations ('ru' or 'en', default: 'ru')
        format_type: Output format ('console', 'plain', 'json', default: 'console')
        **kwargs: Additional formatting parameters:
            - use_colors: Whether to use colors in console output (default: True)
            - show_original_error: Whether to show original error message (default: True)
            - show_traceback: Whether to show traceback (default: False)
    
    Raises:
        TypeError: If exception parameter is not an Exception instance
        ValueError: If language or format_type parameters are invalid
    
    Examples:
        >>> try:
        ...     result = 10 / 0
        ... except Exception as e:
        ...     explain_error(e)
        
        >>> explain_error(TypeError("'str' object cannot be interpreted as an integer"))
        
        >>> explain_error(ValueError("invalid literal"), format_type='json')
    """
    # Parameter validation with custom exceptions
    if not isinstance(exception, Exception):
        raise TypeError(f"Параметр 'exception' должен быть экземпляром Exception, "
                       f"получен {type(exception).__name__}")
    
    # Validate language parameter
    valid_languages = ['ru', 'en']
    if language not in valid_languages:
        raise ValueError(f"Параметр 'language' должен быть одним из {valid_languages}, "
                        f"получен '{language}'")
    
    # Validate format_type parameter
    valid_formats = ['console', 'plain', 'json']
    if format_type not in valid_formats:
        raise ValueError(f"Параметр 'format_type' должен быть одним из {valid_formats}, "
                        f"получен '{format_type}'")
    
    try:
        from .formatters import get_formatter
        
        # Create configuration based on parameters
        config = ExplainerConfig(
            language=language,
            format_type=format_type,
            use_colors=kwargs.get('use_colors', True),
            show_original_error=kwargs.get('show_original_error', True),
            show_traceback=kwargs.get('show_traceback', False)
        )
        
        # Create explainer and get explanation
        explainer = ErrorExplainer(config)
        explanation = explainer.explain(exception)
        
        # Get appropriate formatter and format output
        formatter = get_formatter(format_type, use_colors=config.use_colors)
        formatted_output = formatter.format(explanation)
        
        # Output to console by default
        print(formatted_output)
        
    except ExplanationError as e:
        # Handle explanation-specific errors gracefully
        print(f"Ошибка при объяснении исключения: {e.get_full_message()}")
        print(f"Оригинальная ошибка: {type(exception).__name__}: {exception}")
        if e.original_error:
            print(f"Техническая информация: {e.original_error}")
        
    except FormattingError as e:
        # Handle formatting errors - try to show basic explanation
        print(f"Ошибка форматирования: {e.get_full_message()}")
        try:
            # Try to create a basic explanation without formatting
            explainer = ErrorExplainer()
            explanation = explainer.explain(exception)
            print(f"Простое объяснение: {explanation.simple_explanation}")
            print(f"Совет: {explanation.fix_tip}")
        except Exception:
            print(f"Оригинальная ошибка: {type(exception).__name__}: {exception}")
        
    except ConfigurationError as e:
        # Handle configuration errors
        print(f"Ошибка конфигурации: {e.get_full_message()}")
        print(f"Оригинальная ошибка: {type(exception).__name__}: {exception}")
        
    except FishertoolsError as e:
        # Handle any other fishertools-specific errors
        print(f"Ошибка fishertools: {e.get_full_message()}")
        print(f"Оригинальная ошибка: {type(exception).__name__}: {exception}")
        
    except Exception as e:
        # Ultimate fallback for any unexpected errors
        print(f"Неожиданная ошибка в fishertools: {e}")
        print(f"Оригинальная ошибка: {type(exception).__name__}: {exception}")
        print("Пожалуйста, сообщите об этой проблеме разработчикам fishertools.")