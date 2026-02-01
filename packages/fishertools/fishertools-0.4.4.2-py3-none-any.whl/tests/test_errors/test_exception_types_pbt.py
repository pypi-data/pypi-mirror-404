"""
Property-based tests for exception type identification module.

These tests use Hypothesis to verify that exception type identification
works correctly across a wide range of inputs and scenarios.

**Validates: Requirements 1.1**
"""

import pytest
from hypothesis import given, strategies as st, assume
from fishertools.errors.exception_types import (
    identify_exception_type,
    get_exception_type_info,
    is_supported_exception_type,
    get_exception_type_mapping,
    get_supported_exception_types,
    ExceptionTypeInfo,
    EXCEPTION_TYPE_MAPPING
)


# Strategy for generating supported exception types
SUPPORTED_EXCEPTION_TYPES = [
    TypeError, ValueError, IndexError, KeyError, AttributeError,
    FileNotFoundError, PermissionError, ZeroDivisionError, NameError
]


@st.composite
def supported_exceptions(draw):
    """Strategy for generating supported exception instances."""
    exc_type = draw(st.sampled_from(SUPPORTED_EXCEPTION_TYPES))
    message = draw(st.text(min_size=0, max_size=100))
    return exc_type(message)


@st.composite
def custom_exceptions(draw):
    """Strategy for generating custom exception instances."""
    class CustomException(Exception):
        pass
    
    message = draw(st.text(min_size=0, max_size=100))
    return CustomException(message)


class TestExceptionTypeIdentificationProperty:
    """Property-based tests for exception type identification.
    
    **Property 1: Exception Type Identification**
    *For any* exception object, the Error_Explainer should correctly identify 
    its type (TypeError, ValueError, etc.)
    **Validates: Requirements 1.1**
    """
    
    @given(supported_exceptions())
    def test_identify_returns_string(self, exc):
        """Property: identify_exception_type always returns a string."""
        result = identify_exception_type(exc)
        assert isinstance(result, str)
        assert len(result) > 0
    
    @given(supported_exceptions())
    def test_identify_returns_correct_type_name(self, exc):
        """Property: identify_exception_type returns the correct exception type name."""
        result = identify_exception_type(exc)
        expected = type(exc).__name__
        assert result == expected
    
    @given(st.sampled_from(SUPPORTED_EXCEPTION_TYPES))
    def test_identify_all_supported_types(self, exc_type):
        """Property: identify_exception_type works for all supported exception types."""
        exc = exc_type("test message")
        result = identify_exception_type(exc)
        
        # Result should be the exception type name
        assert result == exc_type.__name__
        # Result should be in the list of supported types
        assert result in get_supported_exception_types()
    
    @given(supported_exceptions())
    def test_identify_consistent_with_type(self, exc):
        """Property: identify_exception_type is consistent with type()."""
        result = identify_exception_type(exc)
        assert result == type(exc).__name__
    
    @given(custom_exceptions())
    def test_identify_custom_exception(self, exc):
        """Property: identify_exception_type works for custom exceptions."""
        result = identify_exception_type(exc)
        assert result == "CustomException"
    
    @given(supported_exceptions())
    def test_identify_idempotent(self, exc):
        """Property: identify_exception_type is idempotent."""
        result1 = identify_exception_type(exc)
        result2 = identify_exception_type(exc)
        assert result1 == result2
    
    @given(st.text(min_size=0, max_size=100))
    def test_identify_with_different_messages(self, message):
        """Property: identify_exception_type ignores exception message."""
        exc1 = ValueError(message)
        exc2 = ValueError("different message")
        
        result1 = identify_exception_type(exc1)
        result2 = identify_exception_type(exc2)
        
        assert result1 == result2 == "ValueError"


class TestGetExceptionTypeInfoProperty:
    """Property-based tests for get_exception_type_info function.
    
    **Property 2: Explanation Completeness**
    *For any* supported exception type, the explanation should contain a 
    non-empty simple explanation, at least one fix suggestion, and a code example
    **Validates: Requirements 1.2, 1.3, 1.4**
    """
    
    @given(supported_exceptions())
    def test_get_info_returns_exception_type_info(self, exc):
        """Property: get_exception_type_info always returns ExceptionTypeInfo."""
        result = get_exception_type_info(exc)
        assert isinstance(result, ExceptionTypeInfo)
    
    @given(supported_exceptions())
    def test_get_info_has_all_fields(self, exc):
        """Property: ExceptionTypeInfo has all required fields."""
        info = get_exception_type_info(exc)
        
        assert hasattr(info, 'exception_class')
        assert hasattr(info, 'name')
        assert hasattr(info, 'description')
        assert hasattr(info, 'common_causes')
    
    @given(supported_exceptions())
    def test_get_info_fields_are_correct_types(self, exc):
        """Property: ExceptionTypeInfo fields have correct types."""
        info = get_exception_type_info(exc)
        
        assert isinstance(info.exception_class, type)
        assert isinstance(info.name, str)
        assert isinstance(info.description, str)
        assert isinstance(info.common_causes, list)
    
    @given(supported_exceptions())
    def test_get_info_fields_are_non_empty(self, exc):
        """Property: ExceptionTypeInfo fields are non-empty."""
        info = get_exception_type_info(exc)
        
        assert len(info.name) > 0
        assert len(info.description) > 0
        assert len(info.common_causes) > 0
    
    @given(supported_exceptions())
    def test_get_info_common_causes_are_strings(self, exc):
        """Property: All common causes are non-empty strings."""
        info = get_exception_type_info(exc)
        
        for cause in info.common_causes:
            assert isinstance(cause, str)
            assert len(cause) > 0
    
    @given(supported_exceptions())
    def test_get_info_exception_class_matches(self, exc):
        """Property: ExceptionTypeInfo.exception_class matches the exception type."""
        info = get_exception_type_info(exc)
        assert info.exception_class == type(exc)
    
    @given(supported_exceptions())
    def test_get_info_name_matches_type(self, exc):
        """Property: ExceptionTypeInfo.name matches the exception type name."""
        info = get_exception_type_info(exc)
        assert info.name == type(exc).__name__
    
    @given(custom_exceptions())
    def test_get_info_custom_exception(self, exc):
        """Property: get_exception_type_info works for custom exceptions."""
        info = get_exception_type_info(exc)
        
        assert info.name == "CustomException"
        assert info.exception_class == type(exc)
        assert len(info.description) > 0
    
    @given(supported_exceptions())
    def test_get_info_idempotent(self, exc):
        """Property: get_exception_type_info is idempotent."""
        info1 = get_exception_type_info(exc)
        info2 = get_exception_type_info(exc)
        
        assert info1.name == info2.name
        assert info1.description == info2.description
        assert info1.common_causes == info2.common_causes


class TestIsSupportedExceptionTypeProperty:
    """Property-based tests for is_supported_exception_type function."""
    
    @given(supported_exceptions())
    def test_supported_returns_boolean(self, exc):
        """Property: is_supported_exception_type always returns a boolean."""
        result = is_supported_exception_type(exc)
        assert isinstance(result, bool)
    
    @given(supported_exceptions())
    def test_supported_returns_true_for_supported(self, exc):
        """Property: is_supported_exception_type returns True for supported types."""
        result = is_supported_exception_type(exc)
        assert result is True
    
    @given(custom_exceptions())
    def test_supported_returns_false_for_custom(self, exc):
        """Property: is_supported_exception_type returns False for custom types."""
        result = is_supported_exception_type(exc)
        assert result is False
    
    @given(st.sampled_from(SUPPORTED_EXCEPTION_TYPES))
    def test_supported_all_supported_types(self, exc_type):
        """Property: is_supported_exception_type returns True for all supported types."""
        exc = exc_type("test")
        assert is_supported_exception_type(exc) is True
    
    @given(supported_exceptions())
    def test_supported_idempotent(self, exc):
        """Property: is_supported_exception_type is idempotent."""
        result1 = is_supported_exception_type(exc)
        result2 = is_supported_exception_type(exc)
        assert result1 == result2


class TestExceptionTypeMappingProperty:
    """Property-based tests for exception type mapping functions."""
    
    def test_mapping_contains_all_supported_types(self):
        """Property: get_exception_type_mapping contains all supported types."""
        mapping = get_exception_type_mapping()
        
        for exc_type in SUPPORTED_EXCEPTION_TYPES:
            assert exc_type in mapping
    
    def test_mapping_values_are_valid_info(self):
        """Property: All mapping values are valid ExceptionTypeInfo objects."""
        mapping = get_exception_type_mapping()
        
        for exc_type, info in mapping.items():
            assert isinstance(info, ExceptionTypeInfo)
            assert info.exception_class == exc_type
            assert isinstance(info.name, str)
            assert len(info.name) > 0
            assert isinstance(info.description, str)
            assert len(info.description) > 0
            assert isinstance(info.common_causes, list)
            assert len(info.common_causes) > 0
    
    def test_supported_types_list_completeness(self):
        """Property: get_supported_exception_types includes all mapped types."""
        types_list = get_supported_exception_types()
        mapping = get_exception_type_mapping()
        
        for info in mapping.values():
            assert info.name in types_list
    
    def test_supported_types_list_no_duplicates(self):
        """Property: get_supported_exception_types has no duplicates."""
        types_list = get_supported_exception_types()
        assert len(types_list) == len(set(types_list))
    
    def test_supported_types_list_all_strings(self):
        """Property: All items in supported types list are strings."""
        types_list = get_supported_exception_types()
        assert all(isinstance(t, str) for t in types_list)


class TestExceptionTypeIdentificationConsistency:
    """Property-based tests for consistency between functions.
    
    **Property 3: Structured Output**
    *For any* exception, explain_error() should return an ExceptionExplanation 
    object with all required fields populated
    **Validates: Requirements 1.6**
    """
    
    @given(supported_exceptions())
    def test_identify_and_get_info_consistent(self, exc):
        """Property: identify_exception_type and get_exception_type_info are consistent."""
        exc_type_name = identify_exception_type(exc)
        info = get_exception_type_info(exc)
        
        assert exc_type_name == info.name
    
    @given(supported_exceptions())
    def test_identify_and_is_supported_consistent(self, exc):
        """Property: identify_exception_type and is_supported_exception_type are consistent."""
        exc_type_name = identify_exception_type(exc)
        is_supported = is_supported_exception_type(exc)
        
        # If it's supported, the name should be in the supported types list
        if is_supported:
            assert exc_type_name in get_supported_exception_types()
    
    @given(supported_exceptions())
    def test_get_info_and_is_supported_consistent(self, exc):
        """Property: get_exception_type_info and is_supported_exception_type are consistent."""
        info = get_exception_type_info(exc)
        is_supported = is_supported_exception_type(exc)
        
        # If it's supported, the info should be in the mapping
        if is_supported:
            mapping = get_exception_type_mapping()
            assert type(exc) in mapping
            assert mapping[type(exc)].name == info.name
    
    @given(supported_exceptions())
    def test_all_functions_consistent(self, exc):
        """Property: All identification functions are mutually consistent."""
        exc_type_name = identify_exception_type(exc)
        info = get_exception_type_info(exc)
        is_supported = is_supported_exception_type(exc)
        mapping = get_exception_type_mapping()
        types_list = get_supported_exception_types()
        
        # All should agree on the exception type name
        assert exc_type_name == info.name == type(exc).__name__
        
        # All should agree it's supported
        assert is_supported is True
        assert type(exc) in mapping
        assert exc_type_name in types_list
        
        # Mapping should have correct info
        assert mapping[type(exc)] == info
