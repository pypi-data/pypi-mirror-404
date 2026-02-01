"""
Integration tests for fishertools.

These tests verify that all components work together correctly,
from exception handling to formatted output.
"""

import pytest
import io
import sys
from contextlib import redirect_stdout
from unittest.mock import patch

import fishertools
from fishertools import explain_error
from fishertools.errors import ErrorExplainer, ErrorExplanation
from fishertools.errors.formatters import get_formatter


class TestMainAPIIntegration:
    """Test the main API integration and complete workflow."""
    
    def test_explain_error_complete_workflow(self):
        """Test complete workflow from exception to formatted output."""
        # Create a test exception
        test_exception = ValueError("invalid literal for int() with base 10: 'abc'")
        
        # Capture output
        output_buffer = io.StringIO()
        
        with redirect_stdout(output_buffer):
            explain_error(test_exception)
        
        output = output_buffer.getvalue()
        
        # Verify output contains expected sections
        assert "Ошибка Python: ValueError" in output
        assert "Что это означает" in output
        assert "Как исправить" in output
        assert "Пример" in output
        assert "invalid literal for int()" in output
    
    def test_explain_error_with_different_formats(self):
        """Test explain_error with different output formats."""
        test_exception = TypeError("'str' object cannot be interpreted as an integer")
        
        # Test console format (default)
        output_buffer = io.StringIO()
        with redirect_stdout(output_buffer):
            explain_error(test_exception, format_type='console')
        console_output = output_buffer.getvalue()
        assert "🚨 Ошибка Python:" in console_output
        
        # Test plain format
        output_buffer = io.StringIO()
        with redirect_stdout(output_buffer):
            explain_error(test_exception, format_type='plain')
        plain_output = output_buffer.getvalue()
        assert "Ошибка Python:" in plain_output
        assert "🚨" not in plain_output  # No emojis in plain format
        
        # Test JSON format
        output_buffer = io.StringIO()
        with redirect_stdout(output_buffer):
            explain_error(test_exception, format_type='json')
        json_output = output_buffer.getvalue()
        assert '"error_type": "TypeError"' in json_output
        assert '"simple_explanation"' in json_output
    
    def test_explain_error_parameter_validation(self):
        """Test that explain_error validates parameters correctly."""
        # Test invalid exception parameter
        with pytest.raises(TypeError, match="должен быть экземпляром Exception"):
            explain_error("not an exception")
        
        # Test invalid language parameter
        with pytest.raises(ValueError, match="должен быть одним из"):
            explain_error(ValueError("test"), language='invalid')
        
        # Test invalid format_type parameter
        with pytest.raises(ValueError, match="должен быть одним из"):
            explain_error(ValueError("test"), format_type='invalid')
    
    def test_explain_error_with_optional_parameters(self):
        """Test explain_error with various optional parameters."""
        test_exception = IndexError("list index out of range")
        
        # Test with colors disabled
        output_buffer = io.StringIO()
        with redirect_stdout(output_buffer):
            explain_error(test_exception, use_colors=False)
        output = output_buffer.getvalue()
        assert "IndexError" in output
        
        # Test with original error hidden
        output_buffer = io.StringIO()
        with redirect_stdout(output_buffer):
            explain_error(test_exception, show_original_error=False)
        output = output_buffer.getvalue()
        # Should still contain explanation but format might differ
        assert "Что это означает" in output


class TestComponentIntegration:
    """Test integration between different components."""
    
    def test_explainer_formatter_integration(self):
        """Test that ErrorExplainer works correctly with formatters."""
        explainer = ErrorExplainer()
        test_exception = KeyError("'missing_key'")
        
        # Get explanation
        explanation = explainer.explain(test_exception)
        
        # Test with different formatters
        console_formatter = get_formatter('console')
        plain_formatter = get_formatter('plain')
        json_formatter = get_formatter('json')
        
        console_output = console_formatter.format(explanation)
        plain_output = plain_formatter.format(explanation)
        json_output = json_formatter.format(explanation)
        
        # All should contain the error information
        assert "KeyError" in console_output
        assert "KeyError" in plain_output
        assert '"error_type": "KeyError"' in json_output
        
        # Console should have formatting
        assert "🚨" in console_output or "═══" in console_output
        
        # Plain should be simpler
        assert "🚨" not in plain_output
        
        # JSON should be valid JSON structure
        import json
        json_data = json.loads(json_output)
        assert json_data['error_type'] == 'KeyError'
    
    def test_pattern_matching_integration(self):
        """Test that pattern matching works with real exceptions."""
        explainer = ErrorExplainer()
        
        # Test common exceptions that should have specific patterns
        test_cases = [
            (TypeError("'str' object cannot be interpreted as an integer"), "TypeError"),
            (ValueError("invalid literal for int()"), "ValueError"),
            (AttributeError("'str' object has no attribute 'append'"), "AttributeError"),
            (IndexError("list index out of range"), "IndexError"),
            (KeyError("'missing_key'"), "KeyError"),
        ]
        
        for exception, expected_type in test_cases:
            explanation = explainer.explain(exception)
            assert explanation.error_type == expected_type
            assert explanation.simple_explanation is not None
            assert explanation.fix_tip is not None
            assert explanation.code_example is not None
    
    def test_fallback_explanation_integration(self):
        """Test that fallback explanations work for unknown exceptions."""
        explainer = ErrorExplainer()
        
        # Create a custom exception that shouldn't have a specific pattern
        class CustomException(Exception):
            pass
        
        custom_exception = CustomException("This is a custom error")
        explanation = explainer.explain(custom_exception)
        
        # Should get fallback explanation
        assert explanation.error_type == "CustomException"
        assert "Произошла ошибка типа CustomException" in explanation.simple_explanation
        assert explanation.fix_tip is not None
        assert explanation.code_example is not None


class TestModuleAccessibility:
    """Test that all modules and functions are accessible through the main API."""
    
    def test_main_api_accessibility(self):
        """Test that main API functions are accessible."""
        # Primary API
        assert hasattr(fishertools, 'explain_error')
        assert callable(fishertools.explain_error)
        
        # Safe utilities
        assert hasattr(fishertools, 'safe_get')
        assert hasattr(fishertools, 'safe_divide')
        assert hasattr(fishertools, 'safe_read_file')
        
        # Learning tools
        assert hasattr(fishertools, 'generate_example')
        assert hasattr(fishertools, 'show_best_practice')
        
        # All should be callable
        assert callable(fishertools.safe_get)
        assert callable(fishertools.safe_divide)
        assert callable(fishertools.generate_example)
        assert callable(fishertools.show_best_practice)
    
    def test_module_imports_accessibility(self):
        """Test that modules can be imported and used."""
        # Test errors module
        from fishertools import errors
        assert hasattr(errors, 'explain_error')
        assert hasattr(errors, 'ErrorExplainer')
        
        # Test safe module
        from fishertools import safe
        assert hasattr(safe, 'safe_get')
        assert hasattr(safe, 'safe_divide')
        
        # Test learn module
        from fishertools import learn
        assert hasattr(learn, 'generate_example')
        assert hasattr(learn, 'show_best_practice')
        
        # Test legacy module
        from fishertools import legacy
        assert legacy is not None
    
    def test_direct_imports_work(self):
        """Test that direct imports from fishertools work."""
        # These should all work without errors
        from fishertools import explain_error
        from fishertools import safe_get, safe_divide
        from fishertools import generate_example, show_best_practice
        
        # Test that they're the same objects as module attributes
        assert explain_error is fishertools.explain_error
        assert safe_get is fishertools.safe_get
        assert generate_example is fishertools.generate_example


class TestErrorHandlingIntegration:
    """Test error handling across the integrated system."""
    
    def test_graceful_error_handling(self):
        """Test that the system handles errors gracefully."""
        # Test with a problematic exception that might cause issues
        test_exception = Exception("Test exception with unicode: тест")
        
        # Should not raise an exception
        output_buffer = io.StringIO()
        with redirect_stdout(output_buffer):
            explain_error(test_exception)
        
        output = output_buffer.getvalue()
        assert len(output) > 0  # Should produce some output
        assert "Exception" in output
    
    def test_system_robustness(self):
        """Test system robustness with edge cases."""
        # Test with exception with empty message
        empty_exception = ValueError("")
        output_buffer = io.StringIO()
        with redirect_stdout(output_buffer):
            explain_error(empty_exception)
        output = output_buffer.getvalue()
        assert "ValueError" in output
        
        # Test with exception with very long message
        long_message = "x" * 1000
        long_exception = RuntimeError(long_message)
        output_buffer = io.StringIO()
        with redirect_stdout(output_buffer):
            explain_error(long_exception)
        output = output_buffer.getvalue()
        assert "RuntimeError" in output


class TestBackwardCompatibility:
    """Test that backward compatibility is maintained."""
    
    def test_legacy_module_access(self):
        """Test that legacy modules are still accessible."""
        # These should work for backward compatibility
        import fishertools.utils
        import fishertools.decorators
        import fishertools.helpers
        
        # Modules should be importable
        assert fishertools.utils is not None
        assert fishertools.decorators is not None
        assert fishertools.helpers is not None
    
    def test_legacy_functions_accessible(self):
        """Test that legacy functions are accessible through fishertools."""
        # Legacy modules should be in __all__
        assert 'utils' in fishertools.__all__
        assert 'decorators' in fishertools.__all__
        assert 'helpers' in fishertools.__all__
        
        # Should be accessible as attributes
        assert hasattr(fishertools, 'utils')
        assert hasattr(fishertools, 'decorators')
        assert hasattr(fishertools, 'helpers')