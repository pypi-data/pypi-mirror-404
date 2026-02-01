"""
Explanation builder for error explanation system.

This module handles creation of error explanations,
separating concerns from the main ErrorExplainer class.
"""

from typing import Optional
from .models import ErrorExplanation, ErrorPattern, ExceptionExplanation
from .exceptions import ExplanationError


class ExplanationBuilder:
    """
    Builds error explanations from patterns and exceptions.
    
    Responsibilities:
    - Create explanations from patterns
    - Create fallback explanations
    - Create emergency explanations
    - Handle explanation errors gracefully
    """
    
    def create_from_pattern(
        self,
        exception: Exception,
        pattern: ErrorPattern
    ) -> ErrorExplanation:
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
            raise ExplanationError(
                f"Не удалось создать объяснение из паттерна: {e}",
                exception_type=type(exception).__name__,
                original_error=e
            )
    
    def create_fallback(self, exception: Exception) -> ErrorExplanation:
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
            return self.create_emergency(exception, e)
    
    def create_emergency(
        self,
        exception: Exception,
        original_error: Exception
    ) -> ErrorExplanation:
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
    
    def create_structured_from_basic(
        self,
        error_explanation: ErrorExplanation
    ) -> ExceptionExplanation:
        """
        Convert basic ErrorExplanation to structured ExceptionExplanation.
        
        Args:
            error_explanation: Basic error explanation
            
        Returns:
            Structured ExceptionExplanation
        """
        return ExceptionExplanation(
            exception_type=error_explanation.error_type,
            simple_explanation=error_explanation.simple_explanation,
            fix_suggestions=[error_explanation.fix_tip],
            code_example=error_explanation.code_example,
            traceback_context=error_explanation.additional_info
        )
    
    def create_emergency_structured(
        self,
        exception: Exception,
        original_error: Exception
    ) -> ExceptionExplanation:
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
