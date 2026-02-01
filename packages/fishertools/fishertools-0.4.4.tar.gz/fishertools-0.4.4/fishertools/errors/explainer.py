"""
Main error explainer implementation.

This module contains the ErrorExplainer class and explain_error function.
"""

from typing import Optional, List
from .models import ErrorExplanation, ExplainerConfig, ErrorPattern, ExceptionExplanation
from .patterns import load_default_patterns
from .exceptions import ExplanationError, FormattingError, ConfigurationError, FishertoolsError


class ErrorExplainer:
    """
    Main class for explaining Python errors in simple terms.
    
    Uses pattern matching to provide contextual explanations for different
    types of Python exceptions.
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
            self.patterns = self._load_patterns()
        except Exception as e:
            if isinstance(e, (ConfigurationError, ExplanationError)):
                raise
            raise ExplanationError(f"Не удалось инициализировать ErrorExplainer: {e}", original_error=e)
    
    def _load_patterns(self) -> List[ErrorPattern]:
        """
        Load error patterns for matching exceptions.
        
        Returns:
            List of ErrorPattern objects
            
        Raises:
            ExplanationError: If patterns cannot be loaded
        """
        try:
            return load_default_patterns()
        except Exception as e:
            raise ExplanationError(f"Не удалось загрузить паттерны ошибок: {e}", original_error=e)
    
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
            raise ExplanationError(f"Параметр должен быть экземпляром Exception, получен {type(exception).__name__}")
        
        try:
            # Try to find a matching pattern
            pattern = self._match_pattern(exception)
            
            if pattern:
                return self._create_explanation_from_pattern(exception, pattern)
            else:
                return self._create_fallback_explanation(exception)
                
        except Exception as e:
            if isinstance(e, ExplanationError):
                raise
            # Graceful degradation - create a minimal explanation if all else fails
            return self._create_emergency_explanation(exception, e)
    
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
            raise ExplanationError(f"Параметр должен быть экземпляром Exception, получен {type(exception).__name__}")
        
        try:
            # Get the basic explanation
            error_explanation = self.explain(exception)
            
            # Convert to structured format
            return ExceptionExplanation(
                exception_type=error_explanation.error_type,
                simple_explanation=error_explanation.simple_explanation,
                fix_suggestions=[error_explanation.fix_tip],  # Convert single tip to list
                code_example=error_explanation.code_example,
                traceback_context=error_explanation.additional_info
            )
        except Exception as e:
            if isinstance(e, ExplanationError):
                raise
            # Graceful degradation
            return self._create_emergency_structured_explanation(exception, e)
    
    def _create_emergency_structured_explanation(self, exception: Exception, 
                                                 original_error: Exception) -> ExceptionExplanation:
        """
        Create a minimal structured explanation when all other methods fail.
        
        Args:
            exception: The original exception to explain
            original_error: The error that prevented normal explanation
            
        Returns:
            Minimal ExceptionExplanation that should always work
        """
        try:
            error_type = getattr(type(exception), '__name__', 'Unknown')
            error_message = str(exception) if exception else 'Unknown error'
            
            return ExceptionExplanation(
                exception_type=error_type,
                simple_explanation="An error occurred in your code. Unfortunately, a detailed explanation could not be generated.",
                fix_suggestions=[
                    "Check the error message above and try to find the problem in your code.",
                    "Search for information about this error type in Python documentation.",
                    "Ask for help if you cannot solve the problem yourself."
                ],
                code_example=f"# General error handling:\ntry:\n    # your code\n    pass\nexcept {error_type} as e:\n    print(f'Error: {{e}}')",
                traceback_context=f"Internal fishertools error: {original_error}"
            )
        except Exception:
            # Absolute last resort
            return ExceptionExplanation(
                exception_type="Critical",
                simple_explanation="A critical error occurred in the error explanation system.",
                fix_suggestions=["Contact fishertools developers with a description of the problem."],
                code_example="# Please contact support",
                traceback_context="Critical system error"
            )

    
    def _match_pattern(self, exception: Exception) -> Optional[ErrorPattern]:
        """
        Find the best matching pattern for the given exception.
        
        Args:
            exception: The exception to match
            
        Returns:
            Matching ErrorPattern or None if no match found
        """
        try:
            for pattern in self.patterns:
                if pattern.matches(exception):
                    return pattern
            return None
        except Exception as e:
            # If pattern matching fails, log the error but don't raise
            # This allows fallback explanation to work
            return None
    
    def _create_explanation_from_pattern(self, exception: Exception, 
                                       pattern: ErrorPattern) -> ErrorExplanation:
        """
        Create explanation using a matched pattern.
        
        Args:
            exception: The original exception
            pattern: The matched pattern
            
        Returns:
            ErrorExplanation based on the pattern
            
        Raises:
            ExplanationError: If explanation creation fails
        """
        try:
            return ErrorExplanation(
                original_error=str(exception),
                error_type=type(exception).__name__,
                simple_explanation=pattern.explanation,
                fix_tip=pattern.tip,
                code_example=pattern.example,
                additional_info=f"Частые причины: {', '.join(pattern.common_causes)}"
            )
        except Exception as e:
            raise ExplanationError(f"Не удалось создать объяснение из паттерна: {e}", 
                                 exception_type=type(exception).__name__, original_error=e)
    
    def _create_fallback_explanation(self, exception: Exception) -> ErrorExplanation:
        """
        Create a generic explanation for unsupported exceptions.
        
        Args:
            exception: The exception to explain
            
        Returns:
            Generic ErrorExplanation
        """
        try:
            error_type = type(exception).__name__
            
            return ErrorExplanation(
                original_error=str(exception),
                error_type=error_type,
                simple_explanation=f"Произошла ошибка типа {error_type}. Это означает, что в вашем коде что-то пошло не так.",
                fix_tip="Внимательно прочитайте сообщение об ошибке и проверьте строку кода, где произошла ошибка. Убедитесь, что все переменные определены и имеют правильные типы.",
                code_example=f"# Пример обработки ошибки {error_type}:\ntry:\n    # ваш код здесь\n    pass\nexcept {error_type} as e:\n    print(f'Ошибка: {{e}}')",
                additional_info="Если вы не можете решить проблему самостоятельно, попробуйте поискать информацию об этом типе ошибки в документации Python или задать вопрос на форуме."
            )
        except Exception as e:
            # If even fallback fails, create emergency explanation
            return self._create_emergency_explanation(exception, e)
    
    def _create_emergency_explanation(self, exception: Exception, original_error: Exception) -> ErrorExplanation:
        """
        Create a minimal explanation when all other methods fail.
        
        This is the last resort for graceful degradation.
        
        Args:
            exception: The original exception to explain
            original_error: The error that prevented normal explanation
            
        Returns:
            Minimal ErrorExplanation that should always work
        """
        try:
            error_type = getattr(type(exception), '__name__', 'Unknown')
            error_message = str(exception) if exception else 'Неизвестная ошибка'
            
            return ErrorExplanation(
                original_error=error_message,
                error_type=error_type,
                simple_explanation="Произошла ошибка в вашем коде. К сожалению, не удалось создать подробное объяснение.",
                fix_tip="Проверьте сообщение об ошибке выше и попробуйте найти проблему в коде. Обратитесь за помощью, если не можете решить проблему самостоятельно.",
                code_example="# Общий способ обработки ошибок:\ntry:\n    # ваш код\n    pass\nexcept Exception as e:\n    print(f'Ошибка: {e}')",
                additional_info=f"Внутренняя ошибка fishertools: {original_error}"
            )
        except Exception:
            # Absolute last resort - create explanation with minimal dependencies
            return ErrorExplanation(
                original_error="Критическая ошибка",
                error_type="Critical",
                simple_explanation="Произошла критическая ошибка в системе объяснения ошибок.",
                fix_tip="Обратитесь к разработчикам fishertools с описанием проблемы.",
                code_example="# Обратитесь за помощью",
                additional_info="Критическая ошибка системы"
            )


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