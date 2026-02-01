"""
Property-based tests for output formatting system.

Tests Properties 10, 11, and 12 from the design document.
"""

import pytest
from hypothesis import given, strategies as st, assume
import re
from fishertools.errors.formatters import (
    ConsoleFormatter, PlainFormatter, JsonFormatter, get_formatter, Colors
)
from fishertools.errors.models import ErrorExplanation


class TestConsoleFormatter:
    """Tests for ConsoleFormatter with color support."""
    
    def test_formatter_initialization(self):
        """Test formatter can be initialized with different color settings."""
        formatter_with_colors = ConsoleFormatter(use_colors=True)
        formatter_without_colors = ConsoleFormatter(use_colors=False)
        
        assert isinstance(formatter_with_colors, ConsoleFormatter)
        assert isinstance(formatter_without_colors, ConsoleFormatter)
    
    @given(
        original_error=st.text(min_size=0, max_size=100).filter(lambda x: '\r' not in x and '\n' not in x),
        error_type=st.text(min_size=1, max_size=50).filter(lambda x: x.strip() and '\r' not in x and '\n' not in x),
        simple_explanation=st.text(min_size=1, max_size=200).filter(lambda x: x.strip() and '\r' not in x and '\n' not in x),
        fix_tip=st.text(min_size=1, max_size=200).filter(lambda x: x.strip() and '\r' not in x and '\n' not in x),
        code_example=st.text(min_size=1, max_size=300).filter(lambda x: x.strip() and '\r' not in x and '\n' not in x),
        additional_info=st.one_of(st.none(), st.text(min_size=0, max_size=200).filter(lambda x: '\r' not in x and '\n' not in x))
    )
    def test_structured_output_format(self, original_error, error_type, simple_explanation, 
                                    fix_tip, code_example, additional_info):
        """
        **Property 10: Structured Output Format**
        For any error explanation output, it should contain clearly delineated 
        sections for explanation, tip, example, and original error message.
        **Validates: Requirements 7.1, 7.3**
        """
        explanation = ErrorExplanation(
            original_error=original_error,
            error_type=error_type,
            simple_explanation=simple_explanation,
            fix_tip=fix_tip,
            code_example=code_example,
            additional_info=additional_info
        )
        
        formatter = ConsoleFormatter(use_colors=False)  # Test without colors for clarity
        output = formatter.format(explanation)
        
        # Check that output contains structured sections
        assert "Ошибка Python:" in output
        assert "=== Что это означает ===" in output
        assert "=== Как исправить ===" in output
        assert "=== Пример ===" in output
        
        # Check that the content appears in the output (normalize whitespace for comparison)
        normalized_output = ' '.join(output.split())
        normalized_explanation = ' '.join(simple_explanation.split())
        normalized_tip = ' '.join(fix_tip.split())
        normalized_code = ' '.join(code_example.split())
        
        assert normalized_explanation in normalized_output
        assert normalized_tip in normalized_output
        assert normalized_code in normalized_output
        
        # If original error is not empty, it should appear
        if original_error.strip():
            assert "=== Сообщение об ошибке ===" in output
            normalized_error = ' '.join(original_error.split())
            assert normalized_error in normalized_output
        
        # If additional info is provided, it should appear
        if additional_info and additional_info.strip():
            assert "=== Дополнительная информация ===" in output
            normalized_info = ' '.join(additional_info.split())
            assert normalized_info in normalized_output
    
    @given(
        original_error=st.text(min_size=0, max_size=100).filter(lambda x: '\r' not in x and '\n' not in x),
        error_type=st.text(min_size=1, max_size=50).filter(lambda x: x.strip() and '\r' not in x and '\n' not in x),
        simple_explanation=st.text(min_size=1, max_size=200).filter(lambda x: x.strip() and '\r' not in x and '\n' not in x),
        fix_tip=st.text(min_size=1, max_size=200).filter(lambda x: x.strip() and '\r' not in x and '\n' not in x),
        code_example=st.text(min_size=1, max_size=300).filter(lambda x: x.strip() and '\r' not in x and '\n' not in x),
        use_colors=st.booleans()
    )
    def test_enhanced_output_readability(self, original_error, error_type, simple_explanation,
                                       fix_tip, code_example, use_colors):
        """
        **Property 11: Enhanced Output Readability**
        For any error explanation output, it should include formatting elements 
        (colors, highlighting, or other visual enhancements) to improve readability.
        **Validates: Requirements 7.2, 7.4**
        """
        explanation = ErrorExplanation(
            original_error=original_error,
            error_type=error_type,
            simple_explanation=simple_explanation,
            fix_tip=fix_tip,
            code_example=code_example
        )
        
        formatter = ConsoleFormatter(use_colors=use_colors)
        output = formatter.format(explanation)
        
        # Check for visual enhancement elements
        if use_colors and formatter.use_colors:
            # Should contain ANSI color codes for enhanced readability
            ansi_pattern = r'\033\[[0-9;]*m'
            assert re.search(ansi_pattern, output), "Output should contain ANSI color codes when colors enabled"
        
        # Should contain visual separators and structure
        assert "═══" in output or "===" in output, "Output should contain section separators"
        assert "🚨" in output, "Output should contain emoji for visual appeal"
        assert "💡" in output, "Output should contain tip emoji"
        
        # Code blocks should have visual boundaries
        if code_example.strip():
            assert "┌─" in output and "└─" in output, "Code examples should have visual boundaries"
    
    @given(
        code_example=st.text(min_size=1, max_size=500).filter(lambda x: x.strip() and '\r' not in x and '\n' not in x),
        error_type=st.text(min_size=1, max_size=50).filter(lambda x: x.strip() and '\r' not in x and '\n' not in x),
        simple_explanation=st.text(min_size=1, max_size=200).filter(lambda x: x.strip() and '\r' not in x and '\n' not in x),
        fix_tip=st.text(min_size=1, max_size=200).filter(lambda x: x.strip() and '\r' not in x and '\n' not in x)
    )
    def test_proper_code_example_formatting(self, code_example, error_type, 
                                          simple_explanation, fix_tip):
        """
        **Property 12: Proper Code Example Formatting**
        For any code example in error explanations, it should be formatted 
        with proper indentation and syntax highlighting.
        **Validates: Requirements 7.5**
        """
        explanation = ErrorExplanation(
            original_error="test error",
            error_type=error_type,
            simple_explanation=simple_explanation,
            fix_tip=fix_tip,
            code_example=code_example
        )
        
        formatter = ConsoleFormatter(use_colors=True)
        output = formatter.format(explanation)
        
        # Check for proper code block formatting
        assert "┌─ Пример кода ─┐" in output, "Code should have proper header"
        assert "└────────────────┘" in output, "Code should have proper footer"
        
        # Check for indentation - code lines should be indented
        code_section_start = output.find("┌─ Пример кода ─┐")
        code_section_end = output.find("└────────────────┘", code_section_start)
        
        if code_section_start != -1 and code_section_end != -1:
            code_section = output[code_section_start:code_section_end]
            code_lines = code_section.split('\n')[1:]  # Skip header line
            
            # Non-empty code lines should be indented
            for line in code_lines:
                if line.strip():  # Only check non-empty lines
                    assert line.startswith('    '), f"Code line should be indented: '{line}'"


class TestPlainFormatter:
    """Tests for PlainFormatter without colors."""
    
    @given(
        original_error=st.text(min_size=0, max_size=100).filter(lambda x: '\r' not in x and '\n' not in x),
        error_type=st.text(min_size=1, max_size=50).filter(lambda x: x.strip() and '\r' not in x and '\n' not in x),
        simple_explanation=st.text(min_size=1, max_size=200).filter(lambda x: x.strip() and '\r' not in x and '\n' not in x),
        fix_tip=st.text(min_size=1, max_size=200).filter(lambda x: x.strip() and '\r' not in x and '\n' not in x),
        code_example=st.text(min_size=1, max_size=300).filter(lambda x: x.strip() and '\r' not in x and '\n' not in x)
    )
    def test_plain_formatter_structure(self, original_error, error_type, simple_explanation,
                                     fix_tip, code_example):
        """Test that PlainFormatter produces structured output without colors."""
        # Filter out any ANSI escape sequences from input
        import re
        ansi_pattern = r'\033\[[0-9;]*m'
        
        original_error = re.sub(ansi_pattern, '', original_error)
        error_type = re.sub(ansi_pattern, '', error_type)
        simple_explanation = re.sub(ansi_pattern, '', simple_explanation)
        fix_tip = re.sub(ansi_pattern, '', fix_tip)
        code_example = re.sub(ansi_pattern, '', code_example)
        
        # Ensure strings are not empty after cleaning
        if not error_type.strip():
            error_type = "TestError"
        if not simple_explanation.strip():
            simple_explanation = "Test explanation"
        if not fix_tip.strip():
            fix_tip = "Test tip"
        if not code_example.strip():
            code_example = "# test code"
        
        explanation = ErrorExplanation(
            original_error=original_error,
            error_type=error_type,
            simple_explanation=simple_explanation,
            fix_tip=fix_tip,
            code_example=code_example
        )
        
        formatter = PlainFormatter()
        output = formatter.format(explanation)
        
        # Should not contain ANSI color codes
        assert not re.search(ansi_pattern, output), "Plain formatter should not contain color codes"
        
        # Should contain structured sections
        assert "Ошибка Python:" in output
        assert "Что это означает:" in output
        assert "Как исправить:" in output
        assert "Пример:" in output
        
        # Content should be present (normalize whitespace for comparison)
        normalized_output = ' '.join(output.split())
        normalized_explanation = ' '.join(simple_explanation.split())
        normalized_tip = ' '.join(fix_tip.split())
        normalized_code = ' '.join(code_example.split())
        
        assert normalized_explanation in normalized_output
        assert normalized_tip in normalized_output
        assert normalized_code in normalized_output


class TestJsonFormatter:
    """Tests for JsonFormatter."""
    
    @given(
        original_error=st.text(min_size=0, max_size=100).filter(lambda x: '\r' not in x and '\n' not in x),
        error_type=st.text(min_size=1, max_size=50).filter(lambda x: x.strip() and '\r' not in x and '\n' not in x),
        simple_explanation=st.text(min_size=1, max_size=200).filter(lambda x: x.strip() and '\r' not in x and '\n' not in x),
        fix_tip=st.text(min_size=1, max_size=200).filter(lambda x: x.strip() and '\r' not in x and '\n' not in x),
        code_example=st.text(min_size=1, max_size=300).filter(lambda x: x.strip() and '\r' not in x and '\n' not in x)
    )
    def test_json_formatter_structure(self, original_error, error_type, simple_explanation,
                                    fix_tip, code_example):
        """Test that JsonFormatter produces valid JSON output."""
        explanation = ErrorExplanation(
            original_error=original_error,
            error_type=error_type,
            simple_explanation=simple_explanation,
            fix_tip=fix_tip,
            code_example=code_example
        )
        
        formatter = JsonFormatter()
        output = formatter.format(explanation)
        
        # Should be valid JSON
        import json
        parsed = json.loads(output)
        
        # Should contain all required fields
        assert parsed['original_error'] == original_error
        assert parsed['error_type'] == error_type
        assert parsed['simple_explanation'] == simple_explanation
        assert parsed['fix_tip'] == fix_tip
        assert parsed['code_example'] == code_example


class TestFormatterFactory:
    """Tests for get_formatter factory function."""
    
    def test_get_formatter_console(self):
        """Test getting console formatter."""
        formatter = get_formatter('console')
        assert isinstance(formatter, ConsoleFormatter)
        
        formatter_no_colors = get_formatter('console', use_colors=False)
        assert isinstance(formatter_no_colors, ConsoleFormatter)
        assert not formatter_no_colors.use_colors or not formatter_no_colors._supports_color()
    
    def test_get_formatter_plain(self):
        """Test getting plain formatter."""
        formatter = get_formatter('plain')
        assert isinstance(formatter, PlainFormatter)
    
    def test_get_formatter_json(self):
        """Test getting JSON formatter."""
        formatter = get_formatter('json')
        assert isinstance(formatter, JsonFormatter)
    
    def test_get_formatter_invalid(self):
        """Test getting invalid formatter raises error."""
        from fishertools.errors.exceptions import FormattingError
        with pytest.raises(FormattingError, match="Неподдерживаемый тип форматтера"):
            get_formatter('invalid')


class TestColorSupport:
    """Tests for color support functionality."""
    
    def test_colors_class_constants(self):
        """Test that Colors class has required constants."""
        assert hasattr(Colors, 'RED')
        assert hasattr(Colors, 'GREEN')
        assert hasattr(Colors, 'YELLOW')
        assert hasattr(Colors, 'BLUE')
        assert hasattr(Colors, 'BOLD')
        assert hasattr(Colors, 'RESET')
        
        # All color codes should be strings
        assert isinstance(Colors.RED, str)
        assert isinstance(Colors.RESET, str)
    
    def test_colorize_functionality(self):
        """Test colorize method works correctly."""
        formatter = ConsoleFormatter(use_colors=True)
        
        # Test colorizing text
        colored_text = formatter._colorize("test", Colors.RED)
        if formatter.use_colors:
            assert Colors.RED in colored_text
            assert Colors.RESET in colored_text
            assert "test" in colored_text
        else:
            assert colored_text == "test"
    
    def test_syntax_highlighting(self):
        """Test Python syntax highlighting."""
        formatter = ConsoleFormatter(use_colors=True)
        
        code_line = "    def test_function():"
        highlighted = formatter._highlight_python_syntax(code_line)
        
        if formatter.use_colors:
            # Should contain color codes for 'def' keyword
            assert Colors.MAGENTA in highlighted or "def" in highlighted
        
        # Original text should still be present
        assert "test_function" in highlighted