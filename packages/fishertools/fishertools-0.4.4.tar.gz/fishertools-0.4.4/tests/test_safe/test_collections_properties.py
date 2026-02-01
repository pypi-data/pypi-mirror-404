"""
Property-based tests for safe collection operations.

These tests validate Property 9: Safe Utility Error Prevention
Requirements: 4.1, 4.2
"""

import pytest
from hypothesis import given, strategies as st, assume
from fishertools.safe.collections import safe_get, safe_divide, safe_max, safe_min, safe_sum
from fishertools.errors.exceptions import SafeUtilityError


class TestSafeUtilitiesProperties:
    """Property-based tests for safe utilities."""
    
    @given(
        collection=st.one_of(
            st.lists(st.integers()),
            st.tuples(st.integers()),
            st.dictionaries(st.text(), st.integers()),
            st.text()
        ),
        index=st.one_of(st.integers(), st.text()),
        default=st.integers()
    )
    def test_safe_get_never_raises_index_key_error(self, collection, index, default):
        """
        **Property 9: Safe Utility Error Prevention**
        **Validates: Requirements 4.1, 4.2**
        
        For any collection and index, safe_get should never raise IndexError or KeyError,
        instead returning the default value or raising a helpful SafeUtilityError for invalid types.
        """
        try:
            result = safe_get(collection, index, default)
            # If no exception was raised, the result should be either:
            # 1. The actual value from the collection, or
            # 2. The default value
            assert result is not None or default is None
        except SafeUtilityError as e:
            # These are acceptable - they should contain helpful Russian messages
            error_message = str(e)
            assert len(error_message) > 0
            # Should not be the original Python error messages
            assert "list index out of range" not in error_message
            assert "key error" not in error_message.lower()
        except (IndexError, KeyError):
            # These should never be raised
            pytest.fail("safe_get raised IndexError or KeyError - should return default instead")
    
    @given(
        a=st.one_of(st.integers(), st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10)),
        b=st.one_of(st.integers(), st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10)),
        default=st.one_of(st.integers(), st.floats(allow_nan=False, allow_infinity=False))
    )
    def test_safe_divide_never_raises_zero_division_error(self, a, b, default):
        """
        **Property 9: Safe Utility Error Prevention**
        **Validates: Requirements 4.1, 4.2**
        
        For any numbers a and b, safe_divide should never raise ZeroDivisionError,
        instead returning the default value when b is zero.
        """
        try:
            result = safe_divide(a, b, default)
            if b == 0:
                # When dividing by zero, should return default
                assert result == default
            else:
                # When not dividing by zero, should return actual division
                expected = a / b
                # Handle cases where division might result in very large numbers
                if abs(expected) > 1e15:
                    # For very large results, just check that we got a finite number
                    assert not (result != result)  # Check for NaN
                    assert abs(result) < float('inf')  # Check for infinity
                else:
                    # For normal results, check precision
                    assert abs(result - expected) < 1e-10
        except (TypeError, ValueError) as e:
            # These are acceptable for invalid input types
            error_message = str(e)
            assert len(error_message) > 0
            # Should contain helpful Russian messages
            assert any(word in error_message for word in ["должно", "должен", "получен"])
        except ZeroDivisionError:
            # This should never be raised
            pytest.fail("safe_divide raised ZeroDivisionError - should return default instead")
    
    @given(
        collection=st.lists(st.integers()),
        default=st.integers()
    )
    def test_safe_max_never_raises_value_error(self, collection, default):
        """
        **Property 9: Safe Utility Error Prevention**
        **Validates: Requirements 4.1, 4.2**
        
        For any collection, safe_max should never raise ValueError for empty sequences,
        instead returning the default value.
        """
        try:
            result = safe_max(collection, default)
            if len(collection) == 0:
                assert result == default
            else:
                assert result == max(collection)
        except (TypeError, ValueError) as e:
            # Only acceptable for invalid input types, not empty collections
            error_message = str(e)
            assert "empty sequence" not in error_message.lower()
            assert len(error_message) > 0
    
    @given(
        collection=st.lists(st.integers()),
        default=st.integers()
    )
    def test_safe_min_never_raises_value_error(self, collection, default):
        """
        **Property 9: Safe Utility Error Prevention**
        **Validates: Requirements 4.1, 4.2**
        
        For any collection, safe_min should never raise ValueError for empty sequences,
        instead returning the default value.
        """
        try:
            result = safe_min(collection, default)
            if len(collection) == 0:
                assert result == default
            else:
                assert result == min(collection)
        except (TypeError, ValueError) as e:
            # Only acceptable for invalid input types, not empty collections
            error_message = str(e)
            assert "empty sequence" not in error_message.lower()
            assert len(error_message) > 0
    
    @given(
        collection=st.lists(st.integers()),
        default=st.integers()
    )
    def test_safe_sum_never_raises_type_error_for_empty(self, collection, default):
        """
        **Property 9: Safe Utility Error Prevention**
        **Validates: Requirements 4.1, 4.2**
        
        For any collection, safe_sum should handle empty collections gracefully
        and provide helpful error messages for type mismatches.
        """
        try:
            result = safe_sum(collection, default)
            if len(collection) == 0:
                assert result == default
            else:
                assert result == sum(collection)
        except SafeUtilityError as e:
            # Should provide helpful Russian error messages
            error_message = str(e)
            assert len(error_message) > 0
            # Should not be the original Python error messages
            assert "unsupported operand" not in error_message.lower()
    
    @given(invalid_input=st.one_of(st.none(), st.booleans(), st.complex_numbers()))
    def test_safe_utilities_provide_helpful_error_messages(self, invalid_input):
        """
        **Property 9: Safe Utility Error Prevention**
        **Validates: Requirements 4.1, 4.2**
        
        For any invalid input types, safe utilities should provide helpful error messages
        in Russian rather than cryptic Python exceptions.
        """
        # Test safe_get with invalid collection
        with pytest.raises(SafeUtilityError) as exc_info:
            safe_get(invalid_input, 0)
        
        error_message = str(exc_info.value)
        assert len(error_message) > 0
        # Should contain Russian words indicating helpful explanation
        assert any(word in error_message for word in ["не может", "должна", "должен", "Неподдерживаемый"])
        
        # Test safe_divide with invalid numbers
        if not isinstance(invalid_input, (int, float)):
            with pytest.raises(SafeUtilityError) as exc_info:
                safe_divide(invalid_input, 1)
            
            error_message = str(exc_info.value)
            assert len(error_message) > 0
            assert any(word in error_message for word in ["должно", "должен", "получен"])