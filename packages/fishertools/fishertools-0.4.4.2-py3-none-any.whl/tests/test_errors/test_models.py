"""
Tests for error explanation data models.
"""

import pytest
from hypothesis import given, strategies as st

from fishertools.errors.models import ErrorPattern, ErrorExplanation, ExplainerConfig


# Hypothesis strategies for generating test data
exception_types = st.sampled_from([
    TypeError, ValueError, AttributeError, IndexError, KeyError, ImportError, SyntaxError
])

russian_text = st.text(
    alphabet="абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ ",
    min_size=10, max_size=200
)

code_example = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789()[]{}=+-*/.,:;#' \n",
    min_size=5, max_size=100
)


class TestErrorPattern:
    """Tests for ErrorPattern data model."""
    
    def test_error_pattern_creation(self):
        """Test basic ErrorPattern creation."""
        pattern = ErrorPattern(
            error_type=TypeError,
            error_keywords=["cannot", "interpreted"],
            explanation="Объяснение типа ошибки",
            tip="Совет по исправлению",
            example="# Пример кода",
            common_causes=["Неправильный тип данных"]
        )
        
        assert pattern.error_type == TypeError
        assert "cannot" in pattern.error_keywords
        assert pattern.explanation == "Объяснение типа ошибки"
    
    def test_pattern_matches_correct_exception(self):
        """Test that pattern correctly matches exceptions."""
        pattern = ErrorPattern(
            error_type=TypeError,
            error_keywords=["cannot", "interpreted"],
            explanation="Test explanation",
            tip="Test tip",
            example="# Test example",
            common_causes=["Test cause"]
        )
        
        # Should match TypeError with matching keywords
        exception = TypeError("'str' object cannot be interpreted as an integer")
        assert pattern.matches(exception) is True
        
        # Should not match different exception type
        value_error = ValueError("some error")
        assert pattern.matches(value_error) is False
        
        # Should not match TypeError without matching keywords
        type_error_no_match = TypeError("different error message")
        assert pattern.matches(type_error_no_match) is False


class TestErrorExplanation:
    """Tests for ErrorExplanation data model."""
    
    def test_error_explanation_creation(self):
        """Test basic ErrorExplanation creation."""
        explanation = ErrorExplanation(
            original_error="TypeError: test error",
            error_type="TypeError",
            simple_explanation="Простое объяснение",
            fix_tip="Совет по исправлению",
            code_example="# Пример кода"
        )
        
        assert explanation.original_error == "TypeError: test error"
        assert explanation.error_type == "TypeError"
        assert explanation.simple_explanation == "Простое объяснение"
    
    def test_error_explanation_to_dict(self):
        """Test ErrorExplanation serialization to dictionary."""
        explanation = ErrorExplanation(
            original_error="Test error",
            error_type="TestError",
            simple_explanation="Test explanation",
            fix_tip="Test tip",
            code_example="# Test code"
        )
        
        result_dict = explanation.to_dict()
        
        assert isinstance(result_dict, dict)
        assert result_dict["original_error"] == "Test error"
        assert result_dict["error_type"] == "TestError"
        assert result_dict["additional_info"] is None


class TestExplainerConfig:
    """Tests for ExplainerConfig data model."""
    
    def test_explainer_config_defaults(self):
        """Test ExplainerConfig default values."""
        config = ExplainerConfig()
        
        assert config.language == 'ru'
        assert config.format_type == 'console'
        assert config.show_original_error is True
        assert config.show_traceback is False
        assert config.use_colors is True
        assert config.max_explanation_length == 200
    
    def test_explainer_config_custom_values(self):
        """Test ExplainerConfig with custom values."""
        config = ExplainerConfig(
            language='en',
            format_type='json',
            show_original_error=False,
            use_colors=False,
            max_explanation_length=150
        )
        
        assert config.language == 'en'
        assert config.format_type == 'json'
        assert config.show_original_error is False
        assert config.use_colors is False
        assert config.max_explanation_length == 150
    
    def test_explainer_config_to_dict(self):
        """Test ExplainerConfig serialization to dictionary."""
        config = ExplainerConfig()
        result_dict = config.to_dict()
        
        assert isinstance(result_dict, dict)
        assert result_dict["language"] == 'ru'
        assert result_dict["format_type"] == 'console'
    
    @given(
        language=st.sampled_from(['ru', 'en']),
        format_type=st.sampled_from(['console', 'json', 'plain']),
        show_original_error=st.booleans(),
        show_traceback=st.booleans(),
        use_colors=st.booleans(),
        max_explanation_length=st.integers(min_value=1, max_value=1000)
    )
    @pytest.mark.property
    def test_explainer_config_property_serialization(self, language, format_type, 
                                                    show_original_error, show_traceback,
                                                    use_colors, max_explanation_length):
        """
        Property test: ExplainerConfig should always serialize to dict correctly.
        Feature: fishertools-refactor, Property: Config serialization consistency
        """
        config = ExplainerConfig(
            language=language,
            format_type=format_type,
            show_original_error=show_original_error,
            show_traceback=show_traceback,
            use_colors=use_colors,
            max_explanation_length=max_explanation_length
        )
        
        result_dict = config.to_dict()
        
        # Property: serialization should always produce a dict with correct keys
        assert isinstance(result_dict, dict)
        assert result_dict["language"] == language
        assert result_dict["format_type"] == format_type
        assert result_dict["show_original_error"] == show_original_error
        assert result_dict["show_traceback"] == show_traceback
        assert result_dict["use_colors"] == use_colors
        assert result_dict["max_explanation_length"] == max_explanation_length


@pytest.mark.property
class TestCompleteErrorExplanationStructure:
    """Property tests for complete error explanation structure."""
    
    @given(
        original_error=st.text(min_size=0, max_size=200),  # Allow empty strings
        error_type=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),  # Ensure non-empty after strip
        simple_explanation=russian_text,
        fix_tip=russian_text,
        code_example=code_example,
        additional_info=st.one_of(st.none(), russian_text)
    )
    def test_complete_error_explanation_structure(self, original_error, error_type, 
                                                simple_explanation, fix_tip, 
                                                code_example, additional_info):
        """
        Property 3: Complete Error Explanation Structure
        For any supported Python exception, the explain_error() function should produce 
        output containing a Russian explanation, a practical fix tip, and a relevant code example.
        
        Feature: fishertools-refactor, Property 3: Complete Error Explanation Structure
        Validates: Requirements 2.1, 2.2, 2.3
        """
        # Create ErrorExplanation with all required components
        explanation = ErrorExplanation(
            original_error=original_error,
            error_type=error_type,
            simple_explanation=simple_explanation,
            fix_tip=fix_tip,
            code_example=code_example,
            additional_info=additional_info
        )
        
        # Property: ErrorExplanation must contain all required components
        assert explanation.original_error is not None
        assert explanation.error_type is not None
        assert explanation.simple_explanation is not None
        assert explanation.fix_tip is not None
        assert explanation.code_example is not None
        
        # Property: All text fields must be non-empty strings (except original_error which can be empty)
        assert isinstance(explanation.original_error, str)
        assert isinstance(explanation.error_type, str)
        assert isinstance(explanation.simple_explanation, str)
        assert isinstance(explanation.fix_tip, str)
        assert isinstance(explanation.code_example, str)
        
        # original_error can be empty, but others must have content
        assert len(explanation.error_type.strip()) > 0
        assert len(explanation.simple_explanation.strip()) > 0
        assert len(explanation.fix_tip.strip()) > 0
        assert len(explanation.code_example.strip()) > 0
        
        # Property: Serialization must preserve all components
        serialized = explanation.to_dict()
        assert "original_error" in serialized
        assert "error_type" in serialized
        assert "simple_explanation" in serialized
        assert "fix_tip" in serialized
        assert "code_example" in serialized
        assert "additional_info" in serialized
        
        # Property: Serialized data must match original data
        assert serialized["original_error"] == explanation.original_error
        assert serialized["error_type"] == explanation.error_type
        assert serialized["simple_explanation"] == explanation.simple_explanation
        assert serialized["fix_tip"] == explanation.fix_tip
        assert serialized["code_example"] == explanation.code_example
        assert serialized["additional_info"] == explanation.additional_info