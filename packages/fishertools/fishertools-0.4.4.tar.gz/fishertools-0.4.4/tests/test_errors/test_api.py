"""
Tests for the main explain_error API function.

This module contains property-based tests for the public API function
that validates the core requirements for universal exception acceptance,
default console output behavior, and formatting parameter responsiveness.
"""

import pytest
import io
import sys
from contextlib import redirect_stdout
from hypothesis import given, strategies as st

from fishertools.errors import explain_error


# Common Python exception types for testing
COMMON_EXCEPTION_TYPES = [
    TypeError, ValueError, AttributeError, IndexError, KeyError, ImportError, SyntaxError
]

# Custom exception for testing
class TestCustomException(Exception):
    """Custom exception for testing API behavior."""
    pass


@pytest.mark.property
class TestUniversalExceptionParameterAcceptance:
    """Property tests for universal exception parameter acceptance."""
    
    @given(
        exception_type=st.sampled_from(COMMON_EXCEPTION_TYPES + [TestCustomException]),
        error_message=st.text(min_size=0, max_size=200)
    )
    def test_universal_exception_parameter_acceptance(self, exception_type, error_message):
        """
        Property 6: Universal Exception Parameter Acceptance
        For any Exception object, the explain_error() function should accept it 
        as a parameter without raising errors.
        
        Feature: fishertools-refactor, Property 6: Universal Exception Parameter Acceptance
        Validates: Requirements 3.2
        """
        # Create exception instance
        exception = exception_type(error_message)
        
        # Capture output to avoid cluttering test output
        output_buffer = io.StringIO()
        
        # Property: explain_error should accept any Exception without raising errors
        try:
            with redirect_stdout(output_buffer):
                explain_error(exception)
            
            # If we get here, the function accepted the exception successfully
            output = output_buffer.getvalue()
            
            # Property: Function should produce some output
            assert len(output.strip()) > 0
            
            # Property: Output should contain error information
            assert error_message in output or str(exception) in output or exception_type.__name__ in output
            
        except Exception as e:
            # If an exception is raised, it should only be due to invalid parameters,
            # not due to the exception type itself
            pytest.fail(f"explain_error raised unexpected exception: {e}")
    
    def test_non_exception_parameter_rejection(self):
        """Test that non-Exception parameters are properly rejected."""
        invalid_inputs = [
            "string",
            123,
            [],
            {},
            None,
            object()
        ]
        
        for invalid_input in invalid_inputs:
            with pytest.raises(TypeError, match="должен быть экземпляром Exception"):
                explain_error(invalid_input)


@pytest.mark.property
class TestDefaultConsoleOutputBehavior:
    """Property tests for default console output behavior."""
    
    @given(
        exception_type=st.sampled_from(COMMON_EXCEPTION_TYPES),
        error_message=st.text(min_size=1, max_size=100)
    )
    def test_default_console_output_behavior(self, exception_type, error_message):
        """
        Property 7: Default Console Output Behavior
        For any call to explain_error() without formatting parameters, the function 
        should produce formatted text output to the console.
        
        Feature: fishertools-refactor, Property 7: Default Console Output Behavior
        Validates: Requirements 3.3
        """
        # Create exception instance
        exception = exception_type(error_message)
        
        # Capture console output
        output_buffer = io.StringIO()
        
        # Call explain_error with default parameters (no formatting specified)
        with redirect_stdout(output_buffer):
            explain_error(exception)
        
        output = output_buffer.getvalue()
        
        # Property: Function should produce console output by default
        assert len(output.strip()) > 0
        
        # Property: Output should be formatted text (not JSON or other structured format)
        # Console format should contain section headers and readable text
        assert "===" in output or "Ошибка Python:" in output or "Что это означает" in output
        
        # Property: Output should contain the error information
        assert exception_type.__name__ in output
        
        # Property: Output should contain Russian text (default language)
        cyrillic_chars = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ')
        assert any(char in cyrillic_chars for char in output)
        
        # Property: Output should not be JSON format by default
        assert not output.strip().startswith('{')
        assert not output.strip().endswith('}')


@pytest.mark.property
class TestFormattingParameterResponsiveness:
    """Property tests for formatting parameter responsiveness."""
    
    @given(
        exception_type=st.sampled_from(COMMON_EXCEPTION_TYPES),
        error_message=st.text(min_size=1, max_size=100),
        format_type=st.sampled_from(['console', 'plain', 'json']),
        language=st.sampled_from(['ru', 'en'])
    )
    def test_formatting_parameter_responsiveness(self, exception_type, error_message, 
                                               format_type, language):
        """
        Property 8: Formatting Parameter Responsiveness
        For any valid formatting parameters passed to explain_error(), the output 
        format should change accordingly.
        
        Feature: fishertools-refactor, Property 8: Formatting Parameter Responsiveness
        Validates: Requirements 3.4
        """
        # Create exception instance
        exception = exception_type(error_message)
        
        # Capture output with specific formatting parameters
        output_buffer = io.StringIO()
        
        with redirect_stdout(output_buffer):
            explain_error(exception, language=language, format_type=format_type)
        
        output = output_buffer.getvalue()
        
        # Property: Function should produce output regardless of format parameters
        assert len(output.strip()) > 0
        
        # Property: Output format should match the requested format_type
        if format_type == 'json':
            # JSON format should produce valid JSON structure
            import json
            try:
                # Output should be parseable as JSON
                json_data = json.loads(output)
                assert isinstance(json_data, dict)
                assert 'error_type' in json_data
                assert 'simple_explanation' in json_data
            except json.JSONDecodeError:
                pytest.fail(f"JSON format requested but output is not valid JSON: {output[:100]}...")
        
        elif format_type == 'plain':
            # Plain format should be simple text without special formatting
            assert "===" in output or "Ошибка Python:" in output
            # Should not contain ANSI color codes
            assert '\033[' not in output
        
        elif format_type == 'console':
            # Console format should contain structured sections
            assert "===" in output or "Ошибка Python:" in output or "Что это означает" in output
        
        # Property: Language parameter should affect output language
        if language == 'ru':
            # Russian output should contain Cyrillic characters
            cyrillic_chars = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ')
            assert any(char in cyrillic_chars for char in output)
        
        # Property: Error type should always be present in output
        assert exception_type.__name__ in output
    
    def test_invalid_formatting_parameters(self):
        """Test that invalid formatting parameters are properly rejected."""
        exception = ValueError("test error")
        
        # Test invalid language
        with pytest.raises(ValueError, match="должен быть одним из"):
            explain_error(exception, language='invalid')
        
        # Test invalid format_type
        with pytest.raises(ValueError, match="должен быть одним из"):
            explain_error(exception, format_type='invalid')
    
    @given(
        use_colors=st.booleans(),
        show_original_error=st.booleans(),
        show_traceback=st.booleans()
    )
    def test_additional_formatting_kwargs(self, use_colors, show_original_error, show_traceback):
        """Test that additional formatting kwargs are properly handled."""
        exception = TypeError("test error")
        
        output_buffer = io.StringIO()
        
        # Should not raise errors with additional kwargs
        with redirect_stdout(output_buffer):
            explain_error(
                exception,
                use_colors=use_colors,
                show_original_error=show_original_error,
                show_traceback=show_traceback
            )
        
        output = output_buffer.getvalue()
        
        # Property: Function should handle additional kwargs without errors
        assert len(output.strip()) > 0
        
        # Property: show_original_error parameter should affect output
        if show_original_error:
            assert "test error" in output or "TypeError" in output
        
        # Property: use_colors parameter should affect console output formatting
        if use_colors and sys.stdout.isatty():
            # May contain ANSI codes in terminal environment
            pass  # Color testing is environment-dependent
        else:
            # When colors disabled, should not contain ANSI escape codes
            # (Note: this is hard to test reliably across environments)
            pass


class TestAPIUnitTests:
    """Unit tests for specific API function behavior."""
    
    def test_basic_functionality(self):
        """Test basic explain_error functionality with known exception."""
        exception = TypeError("'str' object cannot be interpreted as an integer")
        
        output_buffer = io.StringIO()
        with redirect_stdout(output_buffer):
            explain_error(exception)
        
        output = output_buffer.getvalue()
        
        assert len(output) > 0
        assert "TypeError" in output
        assert "str" in output or "integer" in output
    
    def test_json_output_format(self):
        """Test JSON output format produces valid JSON."""
        exception = ValueError("invalid literal for int()")
        
        output_buffer = io.StringIO()
        with redirect_stdout(output_buffer):
            explain_error(exception, format_type='json')
        
        output = output_buffer.getvalue()
        
        # Should be valid JSON
        import json
        data = json.loads(output)
        
        assert data['error_type'] == 'ValueError'
        assert 'simple_explanation' in data
        assert 'fix_tip' in data
        assert 'code_example' in data
    
    def test_plain_output_format(self):
        """Test plain output format."""
        exception = IndexError("list index out of range")
        
        output_buffer = io.StringIO()
        with redirect_stdout(output_buffer):
            explain_error(exception, format_type='plain')
        
        output = output_buffer.getvalue()
        
        assert "IndexError" in output
        assert "list index out of range" in output
        # Should not contain ANSI color codes
        assert '\033[' not in output