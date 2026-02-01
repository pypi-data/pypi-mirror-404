"""
Tests for ErrorExplainer class and exception handling.
"""

import pytest
from hypothesis import given, strategies as st

from fishertools.errors.explainer import ErrorExplainer
from fishertools.errors.models import ExplainerConfig


# Common Python exception types for testing
COMMON_EXCEPTION_TYPES = [
    TypeError, ValueError, AttributeError, IndexError, KeyError, ImportError, SyntaxError
]

# Custom exception types for fallback testing
class CustomError(Exception):
    """Custom exception for testing fallback behavior."""
    pass

class AnotherCustomError(Exception):
    """Another custom exception for testing."""
    pass


@pytest.mark.property
class TestComprehensiveExceptionSupport:
    """Property tests for comprehensive exception support."""
    
    @given(
        exception_type=st.sampled_from(COMMON_EXCEPTION_TYPES),
        error_message=st.text(min_size=1, max_size=200)
    )
    def test_comprehensive_exception_support(self, exception_type, error_message):
        """
        Property 4: Comprehensive Exception Support
        For any common Python exception type (TypeError, ValueError, AttributeError, 
        IndexError, KeyError, ImportError, SyntaxError), the Error_Explainer should 
        provide a specific, contextual explanation.
        
        Feature: fishertools-refactor, Property 4: Comprehensive Exception Support
        Validates: Requirements 2.4, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7
        """
        # Create exception instance
        exception = exception_type(error_message)
        
        # Create explainer
        explainer = ErrorExplainer()
        
        # Get explanation
        explanation = explainer.explain(exception)
        
        # Property: Explanation must be generated without errors
        assert explanation is not None
        
        # Property: Explanation must contain all required components
        assert explanation.original_error is not None
        assert explanation.error_type is not None
        assert explanation.simple_explanation is not None
        assert explanation.fix_tip is not None
        assert explanation.code_example is not None
        
        # Property: Error type must match the exception type
        assert explanation.error_type == exception_type.__name__
        
        # Property: Original error must contain the exception message
        assert error_message in explanation.original_error or str(exception) == explanation.original_error
        
        # Property: Explanation must be non-empty and meaningful
        assert len(explanation.simple_explanation.strip()) > 0
        assert len(explanation.fix_tip.strip()) > 0
        assert len(explanation.code_example.strip()) > 0
        
        # Property: Explanation should be in Russian (contains Cyrillic characters)
        cyrillic_chars = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ')
        explanation_text = explanation.simple_explanation + explanation.fix_tip
        assert any(char in cyrillic_chars for char in explanation_text)


@pytest.mark.property  
class TestGracefulFallbackForUnknownExceptions:
    """Property tests for graceful fallback behavior."""
    
    @given(
        error_message=st.text(min_size=1, max_size=200)
    )
    def test_graceful_fallback_for_unknown_exceptions(self, error_message):
        """
        Property 5: Graceful Fallback for Unknown Exceptions
        For any unsupported or custom exception type, the Error_Explainer should 
        provide a generic but helpful message instead of failing.
        
        Feature: fishertools-refactor, Property 5: Graceful Fallback for Unknown Exceptions
        Validates: Requirements 2.5
        """
        # Create custom exception (not in common types)
        exception = CustomError(error_message)
        
        # Create explainer
        explainer = ErrorExplainer()
        
        # Get explanation - should not raise any exceptions
        explanation = explainer.explain(exception)
        
        # Property: Explanation must be generated without errors
        assert explanation is not None
        
        # Property: Explanation must contain all required components
        assert explanation.original_error is not None
        assert explanation.error_type is not None
        assert explanation.simple_explanation is not None
        assert explanation.fix_tip is not None
        assert explanation.code_example is not None
        
        # Property: Error type must match the custom exception type
        assert explanation.error_type == "CustomError"
        
        # Property: Original error must contain the exception message
        assert error_message in explanation.original_error or str(exception) == explanation.original_error
        
        # Property: Fallback explanation must be helpful and non-empty
        assert len(explanation.simple_explanation.strip()) > 0
        assert len(explanation.fix_tip.strip()) > 0
        assert len(explanation.code_example.strip()) > 0
        
        # Property: Fallback should mention the error type
        assert "CustomError" in explanation.simple_explanation or "CustomError" in explanation.code_example
        
        # Property: Fallback should be in Russian
        cyrillic_chars = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ')
        explanation_text = explanation.simple_explanation + explanation.fix_tip
        assert any(char in cyrillic_chars for char in explanation_text)
        
        # Property: Additional info should provide guidance
        if explanation.additional_info:
            assert len(explanation.additional_info.strip()) > 0


class TestExplainerUnitTests:
    """Unit tests for specific explainer functionality."""
    
    def test_explainer_with_config(self):
        """Test explainer initialization with custom config."""
        config = ExplainerConfig(language='en', use_colors=False)
        explainer = ErrorExplainer(config)
        
        assert explainer.config.language == 'en'
        assert explainer.config.use_colors is False
    
    def test_explainer_fallback_behavior(self):
        """Test specific fallback behavior with known custom exception."""
        exception = AnotherCustomError("test message")
        explainer = ErrorExplainer()
        
        explanation = explainer.explain(exception)
        
        assert explanation.error_type == "AnotherCustomError"
        assert "test message" in explanation.original_error
        assert "AnotherCustomError" in explanation.simple_explanation
    
    def test_explainer_handles_empty_patterns(self):
        """Test that explainer works even with no patterns loaded."""
        explainer = ErrorExplainer()
        # Patterns list should be empty since no patterns are defined yet
        assert isinstance(explainer.patterns, list)
        
        # Should still handle exceptions gracefully
        exception = TypeError("test error")
        explanation = explainer.explain(exception)
        
        assert explanation is not None
        assert explanation.error_type == "TypeError"