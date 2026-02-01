"""
Tests for comprehensive error handling system.

This module tests the custom exception classes, graceful degradation,
and error recovery mechanisms in fishertools.
"""

import pytest
import io
from contextlib import redirect_stdout

from fishertools.errors.exceptions import (
    FishertoolsError, ExplanationError, FormattingError, 
    ConfigurationError, PatternError, SafeUtilityError
)
from fishertools.errors.explainer import ErrorExplainer, explain_error
from fishertools.errors.models import ErrorPattern, ErrorExplanation, ExplainerConfig
from fishertools.errors.formatters import get_formatter
from fishertools.safe import safe_get, safe_divide


class TestCustomExceptions:
    """Test custom exception classes and their behavior."""
    
    def test_fishertools_error_base_class(self):
        """Test FishertoolsError base class functionality."""
        # Test basic initialization
        error = FishertoolsError("Test error message")
        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.original_error is None
        
        # Test with original error
        original = ValueError("Original error")
        error_with_original = FishertoolsError("Wrapper error", original)
        assert error_with_original.original_error == original
        
        # Test full message
        full_message = error_with_original.get_full_message()
        assert "Wrapper error" in full_message
        assert "Original error" in full_message
        assert "Причина:" in full_message
    
    def test_explanation_error_specifics(self):
        """Test ExplanationError specific functionality."""
        error = ExplanationError("Explanation failed", exception_type="ValueError")
        assert error.exception_type == "ValueError"
        
        full_message = error.get_full_message()
        assert "Explanation failed" in full_message
        assert "ValueError" in full_message
        assert "Тип исключения:" in full_message
    
    def test_formatting_error_specifics(self):
        """Test FormattingError specific functionality."""
        error = FormattingError("Formatting failed", formatter_type="console")
        assert error.formatter_type == "console"
        
        full_message = error.get_full_message()
        assert "Formatting failed" in full_message
        assert "console" in full_message
        assert "Тип форматтера:" in full_message
    
    def test_configuration_error_specifics(self):
        """Test ConfigurationError specific functionality."""
        error = ConfigurationError("Invalid config", config_field="language", config_value="invalid")
        assert error.config_field == "language"
        assert error.config_value == "invalid"
        
        full_message = error.get_full_message()
        assert "Invalid config" in full_message
        assert "language" in full_message
        assert "invalid" in full_message
        assert "Поле:" in full_message
        assert "Значение:" in full_message
    
    def test_pattern_error_specifics(self):
        """Test PatternError specific functionality."""
        error = PatternError("Pattern failed", pattern_type="TypeError")
        assert error.pattern_type == "TypeError"
        
        full_message = error.get_full_message()
        assert "Pattern failed" in full_message
        assert "TypeError" in full_message
        assert "Тип паттерна:" in full_message
    
    def test_safe_utility_error_specifics(self):
        """Test SafeUtilityError specific functionality."""
        error = SafeUtilityError("Utility failed", utility_name="safe_get")
        assert error.utility_name == "safe_get"
        
        full_message = error.get_full_message()
        assert "Utility failed" in full_message
        assert "safe_get" in full_message
        assert "Утилита:" in full_message


class TestErrorRecovery:
    """Test error recovery and graceful degradation."""
    
    def test_explainer_initialization_recovery(self):
        """Test ErrorExplainer recovery from initialization errors."""
        # Test with invalid config - should raise ConfigurationError
        with pytest.raises(ConfigurationError):
            invalid_config = ExplainerConfig(language="invalid")
            ErrorExplainer(invalid_config)
    
    def test_explanation_fallback_mechanism(self):
        """Test fallback explanation when pattern matching fails."""
        explainer = ErrorExplainer()
        
        # Create a custom exception that won't match any pattern
        class UnknownCustomError(Exception):
            pass
        
        unknown_exception = UnknownCustomError("Unknown error")
        explanation = explainer.explain(unknown_exception)
        
        # Should create fallback explanation
        assert explanation.error_type == "UnknownCustomError"
        assert "Произошла ошибка типа UnknownCustomError" in explanation.simple_explanation
        assert explanation.fix_tip is not None
        assert explanation.code_example is not None
    
    def test_emergency_explanation_creation(self):
        """Test emergency explanation when all else fails."""
        explainer = ErrorExplainer()
        
        # Simulate a scenario where even fallback fails by creating problematic exception
        class ProblematicException(Exception):
            def __str__(self):
                raise RuntimeError("Cannot convert to string")
        
        problematic = ProblematicException()
        
        # Should still create some explanation without crashing
        explanation = explainer.explain(problematic)
        assert explanation is not None
        assert explanation.simple_explanation is not None
        assert explanation.fix_tip is not None
    
    def test_formatter_error_recovery(self):
        """Test recovery from formatter errors."""
        # Test with invalid formatter type
        with pytest.raises(FormattingError):
            get_formatter("invalid_type")
    
    def test_explain_error_graceful_degradation(self):
        """Test explain_error function graceful degradation."""
        # Test with various problematic scenarios
        test_cases = [
            ValueError("Test error"),
            Exception(""),  # Empty message
            RuntimeError("Very long error message " + "x" * 1000),
        ]
        
        for test_exception in test_cases:
            # Should not raise exceptions, should produce output
            output_buffer = io.StringIO()
            with redirect_stdout(output_buffer):
                explain_error(test_exception)
            
            output = output_buffer.getvalue()
            assert len(output) > 0  # Should produce some output
    
    def test_explain_error_parameter_validation(self):
        """Test explain_error parameter validation with custom exceptions."""
        # Test invalid exception parameter
        with pytest.raises(TypeError) as exc_info:
            explain_error("not an exception")
        assert "должен быть экземпляром Exception" in str(exc_info.value)
        
        # Test invalid language parameter
        with pytest.raises(ValueError) as exc_info:
            explain_error(ValueError("test"), language="invalid")
        assert "должен быть одним из" in str(exc_info.value)
        
        # Test invalid format_type parameter
        with pytest.raises(ValueError) as exc_info:
            explain_error(ValueError("test"), format_type="invalid")
        assert "должен быть одним из" in str(exc_info.value)


class TestSafeUtilityErrorHandling:
    """Test error handling in safe utility functions."""
    
    def test_safe_get_error_handling(self):
        """Test safe_get error handling with custom exceptions."""
        # Test with None collection
        with pytest.raises(SafeUtilityError) as exc_info:
            safe_get(None, 0)
        assert "не может быть None" in str(exc_info.value)
        assert exc_info.value.utility_name == "safe_get"
        
        # Test with invalid collection type (number)
        with pytest.raises(SafeUtilityError) as exc_info:
            safe_get(123, 0)  # Number is not a valid collection
        assert "не может быть None или числом" in str(exc_info.value)
        
        # Test with invalid index type for list - now returns default instead of raising
        result = safe_get([1, 2, 3], "invalid_index", default="not found")
        assert result == "not found"  # Pythonic approach: EAFP
    
    def test_safe_divide_error_handling(self):
        """Test safe_divide error handling with custom exceptions."""
        # Test with invalid types (None, bool, complex, str)
        with pytest.raises(SafeUtilityError) as exc_info:
            safe_divide("not_a_number", 2)
        assert "должно быть числом" in str(exc_info.value)
        assert exc_info.value.utility_name == "safe_divide"
        
        with pytest.raises(SafeUtilityError) as exc_info:
            safe_divide(10, "not_a_number")
        assert "должен быть числом" in str(exc_info.value)
        
        # default can be any type now - more flexible
        result = safe_divide(10, 0, default="undefined")
        assert result == "undefined"  # Flexible default value


class TestModelValidationErrors:
    """Test validation errors in data models."""
    
    def test_error_pattern_validation(self):
        """Test ErrorPattern validation with custom exceptions."""
        # Test with empty explanation
        with pytest.raises(PatternError) as exc_info:
            ErrorPattern(
                error_type=ValueError,
                error_keywords=["test"],
                explanation="",  # Empty explanation
                tip="Test tip",
                example="test code",
                common_causes=["test cause"]
            )
        assert "explanation cannot be empty" in str(exc_info.value)
        
        # Test with empty tip
        with pytest.raises(PatternError) as exc_info:
            ErrorPattern(
                error_type=ValueError,
                error_keywords=["test"],
                explanation="Test explanation",
                tip="",  # Empty tip
                example="test code",
                common_causes=["test cause"]
            )
        assert "tip cannot be empty" in str(exc_info.value)
    
    def test_error_explanation_validation(self):
        """Test ErrorExplanation validation with custom exceptions."""
        # Test with None original_error
        with pytest.raises(ExplanationError) as exc_info:
            ErrorExplanation(
                original_error=None,
                error_type="ValueError",
                simple_explanation="Test explanation",
                fix_tip="Test tip",
                code_example="test code"
            )
        assert "original_error cannot be None" in str(exc_info.value)
        
        # Test with empty simple_explanation
        with pytest.raises(ExplanationError) as exc_info:
            ErrorExplanation(
                original_error="Test error",
                error_type="ValueError",
                simple_explanation="",  # Empty explanation
                fix_tip="Test tip",
                code_example="test code"
            )
        assert "simple_explanation cannot be empty" in str(exc_info.value)
    
    def test_explainer_config_validation(self):
        """Test ExplainerConfig validation with custom exceptions."""
        # Test with invalid language
        with pytest.raises(ConfigurationError) as exc_info:
            ExplainerConfig(language="invalid")
        assert "language must be" in str(exc_info.value)
        assert exc_info.value.config_field == "language"
        assert exc_info.value.config_value == "invalid"
        
        # Test with invalid format_type
        with pytest.raises(ConfigurationError) as exc_info:
            ExplainerConfig(format_type="invalid")
        assert "format_type must be" in str(exc_info.value)
        assert exc_info.value.config_field == "format_type"
        
        # Test with invalid max_explanation_length
        with pytest.raises(ConfigurationError) as exc_info:
            ExplainerConfig(max_explanation_length=-1)
        assert "max_explanation_length must be positive" in str(exc_info.value)
        assert exc_info.value.config_field == "max_explanation_length"


class TestErrorHandlingIntegration:
    """Test integration of error handling across the system."""
    
    def test_end_to_end_error_handling(self):
        """Test complete error handling flow from exception to output."""
        # Test with a normal exception
        test_exception = ValueError("Test value error")
        
        output_buffer = io.StringIO()
        with redirect_stdout(output_buffer):
            explain_error(test_exception)
        
        output = output_buffer.getvalue()
        assert len(output) > 0
        assert "ValueError" in output
        assert "Test value error" in output
    
    def test_error_handling_with_different_formatters(self):
        """Test error handling with different output formatters."""
        test_exception = TypeError("Test type error")
        
        # Test with different format types
        for format_type in ['console', 'plain', 'json']:
            output_buffer = io.StringIO()
            with redirect_stdout(output_buffer):
                explain_error(test_exception, format_type=format_type)
            
            output = output_buffer.getvalue()
            assert len(output) > 0
            if format_type == 'json':
                # JSON output should be valid JSON structure
                import json
                try:
                    json.loads(output)
                except json.JSONDecodeError:
                    pytest.fail(f"Invalid JSON output for format_type={format_type}")
    
    def test_exception_hierarchy_catching(self):
        """Test that FishertoolsError can catch all custom exceptions."""
        custom_exceptions = [
            ExplanationError("Test explanation error"),
            FormattingError("Test formatting error"),
            ConfigurationError("Test config error"),
            PatternError("Test pattern error"),
            SafeUtilityError("Test utility error")
        ]
        
        for exc in custom_exceptions:
            # All should be instances of FishertoolsError
            assert isinstance(exc, FishertoolsError)
            
            # Should be catchable with FishertoolsError
            try:
                raise exc
            except FishertoolsError as caught:
                assert caught == exc
            except Exception:
                pytest.fail(f"Exception {type(exc).__name__} not caught by FishertoolsError")