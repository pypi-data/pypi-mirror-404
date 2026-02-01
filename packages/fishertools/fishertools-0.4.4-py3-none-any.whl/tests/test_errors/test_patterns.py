"""
Unit tests for error pattern matching functionality.

Tests specific error patterns and their matching behavior for common Python exceptions.
"""

import pytest
from fishertools.errors.patterns import load_default_patterns, DEFAULT_PATTERNS
from fishertools.errors.explainer import ErrorExplainer
from fishertools.errors.models import ErrorPattern


class TestErrorPatternMatching:
    """Unit tests for specific error pattern matching."""
    
    def test_load_default_patterns(self):
        """Test that default patterns are loaded correctly."""
        patterns = load_default_patterns()
        
        # Should have patterns for all required exception types
        assert len(patterns) > 0
        
        # Check that we have patterns for all required exception types
        exception_types = {pattern.error_type for pattern in patterns}
        required_types = {TypeError, ValueError, AttributeError, IndexError, KeyError, ImportError, SyntaxError}
        
        assert required_types.issubset(exception_types), f"Missing patterns for: {required_types - exception_types}"
    
    def test_type_error_operand_pattern_matching(self):
        """Test TypeError pattern matching for operand type errors."""
        explainer = ErrorExplainer()
        
        # Test unsupported operand type error
        exception = TypeError("unsupported operand type(s) for +: 'int' and 'str'")
        explanation = explainer.explain(exception)
        
        assert explanation.error_type == "TypeError"
        assert "несовместимыми типами" in explanation.simple_explanation
        assert "преобразования типов" in explanation.fix_tip
        assert "int(" in explanation.code_example or "str(" in explanation.code_example
    
    def test_type_error_function_arguments_pattern_matching(self):
        """Test TypeError pattern matching for function argument errors."""
        explainer = ErrorExplainer()
        
        # Test missing positional argument error
        exception = TypeError("greet() missing 1 required positional argument: 'age'")
        explanation = explainer.explain(exception)
        
        assert explanation.error_type == "TypeError"
        assert "неправильным количеством аргументов" in explanation.simple_explanation
        assert "правильное количество аргументов" in explanation.fix_tip
        assert "def " in explanation.code_example
    
    def test_type_error_not_callable_pattern_matching(self):
        """Test TypeError pattern matching for 'not callable' errors."""
        explainer = ErrorExplainer()
        
        # Test object not callable error
        exception = TypeError("'list' object is not callable")
        explanation = explainer.explain(exception)
        
        assert explanation.error_type == "TypeError"
        assert "не является" in explanation.simple_explanation and "функцией" in explanation.simple_explanation
        assert "функцию" in explanation.fix_tip
        assert "len(" in explanation.code_example
    
    def test_value_error_conversion_pattern_matching(self):
        """Test ValueError pattern matching for conversion errors."""
        explainer = ErrorExplainer()
        
        # Test invalid literal for int conversion
        exception = ValueError("invalid literal for int() with base 10: 'abc'")
        explanation = explainer.explain(exception)
        
        assert explanation.error_type == "ValueError"
        assert "преобразовать строку в число" in explanation.simple_explanation
        assert "цифры" in explanation.fix_tip
        assert "isdigit()" in explanation.code_example
    
    def test_value_error_unpacking_pattern_matching(self):
        """Test ValueError pattern matching for unpacking errors."""
        explainer = ErrorExplainer()
        
        # Test too many values to unpack
        exception = ValueError("too many values to unpack (expected 2)")
        explanation = explainer.explain(exception)
        
        assert explanation.error_type == "ValueError"
        assert "Количество переменных" in explanation.simple_explanation
        assert "количество переменных" in explanation.fix_tip
        assert "=" in explanation.code_example
    
    def test_attribute_error_pattern_matching(self):
        """Test AttributeError pattern matching."""
        explainer = ErrorExplainer()
        
        # Test attribute error
        exception = AttributeError("'str' object has no attribute 'append'")
        explanation = explainer.explain(exception)
        
        assert explanation.error_type == "AttributeError"
        assert "атрибуту или методу" in explanation.simple_explanation
        assert "правильность написания" in explanation.fix_tip
        assert "dir()" in explanation.fix_tip
    
    def test_index_error_pattern_matching(self):
        """Test IndexError pattern matching."""
        explainer = ErrorExplainer()
        
        # Test list index out of range
        exception = IndexError("list index out of range")
        explanation = explainer.explain(exception)
        
        assert explanation.error_type == "IndexError"
        assert "индексу, который не существует" in explanation.simple_explanation
        assert "len()" in explanation.fix_tip
        assert "len(" in explanation.code_example
    
    def test_key_error_pattern_matching(self):
        """Test KeyError pattern matching."""
        explainer = ErrorExplainer()
        
        # Test key error
        exception = KeyError("'missing_key'")
        explanation = explainer.explain(exception)
        
        assert explanation.error_type == "KeyError"
        assert "ключу, которого в словаре не существует" in explanation.simple_explanation
        assert "get()" in explanation.fix_tip or "'in'" in explanation.fix_tip
        assert "get(" in explanation.code_example or " in " in explanation.code_example
    
    def test_import_error_pattern_matching(self):
        """Test ImportError pattern matching."""
        explainer = ErrorExplainer()
        
        # Test module not found error
        exception = ImportError("No module named 'nonexistent_module'")
        explanation = explainer.explain(exception)
        
        assert explanation.error_type == "ImportError"
        assert "не может найти модуль" in explanation.simple_explanation
        assert "установлен" in explanation.fix_tip
        assert "pip install" in explanation.code_example or "import" in explanation.code_example
    
    def test_syntax_error_pattern_matching(self):
        """Test SyntaxError pattern matching."""
        explainer = ErrorExplainer()
        
        # Test syntax error
        exception = SyntaxError("invalid syntax")
        explanation = explainer.explain(exception)
        
        assert explanation.error_type == "SyntaxError"
        assert "синтаксическая ошибка" in explanation.simple_explanation
        assert "скобки" in explanation.fix_tip or "отступы" in explanation.fix_tip
        assert ":" in explanation.code_example
    
    def test_file_not_found_error_pattern_matching(self):
        """Test FileNotFoundError pattern matching."""
        explainer = ErrorExplainer()
        
        # Test file not found error
        exception = FileNotFoundError("[Errno 2] No such file or directory: 'data.txt'")
        explanation = explainer.explain(exception)
        
        assert explanation.error_type == "FileNotFoundError"
        assert "не существует" in explanation.simple_explanation
        assert "путь" in explanation.fix_tip or "файл" in explanation.fix_tip
        assert "os.path.exists" in explanation.code_example or "exists" in explanation.code_example
    
    def test_permission_error_pattern_matching(self):
        """Test PermissionError pattern matching."""
        explainer = ErrorExplainer()
        
        # Test permission error
        exception = PermissionError("[Errno 13] Permission denied: 'protected_file.txt'")
        explanation = explainer.explain(exception)
        
        assert explanation.error_type == "PermissionError"
        assert "прав доступа" in explanation.simple_explanation or "Permission" in explanation.simple_explanation
        assert "права" in explanation.fix_tip or "доступ" in explanation.fix_tip
        assert "os.access" in explanation.code_example or "access" in explanation.code_example
    
    def test_zero_division_error_pattern_matching(self):
        """Test ZeroDivisionError pattern matching."""
        explainer = ErrorExplainer()
        
        # Test zero division error
        exception = ZeroDivisionError("division by zero")
        explanation = explainer.explain(exception)
        
        assert explanation.error_type == "ZeroDivisionError"
        assert "ноль" in explanation.simple_explanation
        assert "делитель" in explanation.fix_tip or "ноль" in explanation.fix_tip
        assert "!= 0" in explanation.code_example or "if" in explanation.code_example
    
    def test_name_error_pattern_matching(self):
        """Test NameError pattern matching."""
        explainer = ErrorExplainer()
        
        # Test name error
        exception = NameError("name 'undefined_var' is not defined")
        explanation = explainer.explain(exception)
        
        assert explanation.error_type == "NameError"
        assert "не была определена" in explanation.simple_explanation or "not defined" in explanation.simple_explanation
        assert "определена" in explanation.fix_tip or "defined" in explanation.fix_tip
        assert "=" in explanation.code_example


class TestErrorPatternValidation:
    """Tests for error pattern validation and structure."""
    
    def test_all_patterns_have_required_fields(self):
        """Test that all patterns have required fields populated."""
        patterns = load_default_patterns()
        
        for pattern in patterns:
            assert isinstance(pattern, ErrorPattern)
            assert pattern.error_type is not None
            # Allow empty keywords for certain patterns (like KeyError)
            assert pattern.error_keywords is not None
            assert pattern.explanation.strip() != ""
            assert pattern.tip.strip() != ""
            assert pattern.example.strip() != ""
            assert len(pattern.common_causes) > 0
    
    def test_patterns_have_russian_content(self):
        """Test that all patterns contain Russian text."""
        patterns = load_default_patterns()
        cyrillic_chars = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ')
        
        for pattern in patterns:
            # Check explanation contains Russian text
            assert any(char in cyrillic_chars for char in pattern.explanation)
            # Check tip contains Russian text
            assert any(char in cyrillic_chars for char in pattern.tip)
    
    def test_pattern_matching_logic(self):
        """Test the pattern matching logic works correctly."""
        patterns = load_default_patterns()
        
        # Find a TypeError pattern for operand types
        type_error_pattern = None
        for pattern in patterns:
            if pattern.error_type == TypeError and "operand" in pattern.error_keywords[0]:
                type_error_pattern = pattern
                break
        
        assert type_error_pattern is not None
        
        # Test that it matches appropriate exceptions
        matching_exception = TypeError("unsupported operand type(s) for +: 'int' and 'str'")
        assert type_error_pattern.matches(matching_exception)
        
        # Test that it doesn't match inappropriate exceptions
        non_matching_exception = ValueError("invalid literal")
        assert not type_error_pattern.matches(non_matching_exception)
        
        # Test that it doesn't match TypeError with different message
        different_type_error = TypeError("takes 1 positional argument but 2 were given")
        # This should not match the operand pattern (should match a different TypeError pattern)
        assert not type_error_pattern.matches(different_type_error)
    
    def test_pattern_coverage_for_requirements(self):
        """Test that we have patterns covering all required exception types from requirements."""
        patterns = load_default_patterns()
        covered_types = {pattern.error_type for pattern in patterns}
        
        # Requirements 6.1-6.7 specify these exception types
        required_types = {
            TypeError,     # 6.1
            ValueError,    # 6.2  
            AttributeError, # 6.3
            IndexError,    # 6.4
            KeyError,      # 6.5
            ImportError,   # 6.6
            SyntaxError    # 6.7
        }
        
        assert required_types.issubset(covered_types), f"Missing coverage for: {required_types - covered_types}"
        
        # Ensure we have multiple patterns for TypeError (most common)
        type_error_patterns = [p for p in patterns if p.error_type == TypeError]
        assert len(type_error_patterns) >= 2, "Should have multiple TypeError patterns for different scenarios"


class TestPatternIntegration:
    """Integration tests for patterns with the explainer system."""
    
    def test_explainer_uses_patterns_correctly(self):
        """Test that explainer correctly uses loaded patterns."""
        explainer = ErrorExplainer()
        
        # Verify patterns are loaded
        assert len(explainer.patterns) > 0
        
        # Test with a specific exception that should match a pattern
        exception = TypeError("unsupported operand type(s) for +: 'int' and 'str'")
        explanation = explainer.explain(exception)
        
        # Should get a pattern-based explanation, not fallback
        assert "несовместимыми типами" in explanation.simple_explanation
        assert explanation.additional_info is not None
        assert "Частые причины:" in explanation.additional_info
    
    def test_explainer_fallback_when_no_pattern_matches(self):
        """Test that explainer falls back correctly when no pattern matches."""
        explainer = ErrorExplainer()
        
        # Create an exception that won't match any pattern
        class UnknownError(Exception):
            pass
        
        exception = UnknownError("some unknown error")
        explanation = explainer.explain(exception)
        
        # Should get fallback explanation
        assert "UnknownError" in explanation.simple_explanation
        assert "что-то пошло не так" in explanation.simple_explanation
        assert explanation.additional_info is not None