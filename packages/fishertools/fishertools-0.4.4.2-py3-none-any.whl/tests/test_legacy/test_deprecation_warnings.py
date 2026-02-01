"""
Property-based tests for deprecation warnings

Feature: fishertools-refactor, Property 2: Deprecation Warning Generation
For any deprecated function, calling it should generate a deprecation warning 
while still executing the function.

**Validates: Requirements 1.5**
"""

import pytest
import warnings
from hypothesis import given, strategies as st
import tempfile
import os

from fishertools.legacy import (
    unsafe_file_reader,
    risky_divide, 
    complex_list_operation,
    show_deprecation_info,
    list_deprecated_functions
)
from fishertools.legacy.deprecation import deprecated
import fishertools.legacy as legacy_module


class TestDeprecationWarningGeneration:
    """
    Property 2: Deprecation Warning Generation
    For any deprecated function, calling it should generate a deprecation warning
    while still executing the function
    """
    
    def test_deprecated_functions_generate_warnings(self):
        """Test that all deprecated functions generate warnings when called"""
        deprecated_funcs = list_deprecated_functions(legacy_module)
        
        # Ensure we have deprecated functions to test
        assert len(deprecated_funcs) > 0, "No deprecated functions found for testing"
        
        for func_name in deprecated_funcs:
            func = getattr(legacy_module, func_name)
            
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                
                try:
                    # Call function with appropriate test arguments
                    if func_name == 'unsafe_file_reader':
                        # Create a temporary file for testing
                        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
                            f.write("test content")
                            temp_path = f.name
                        
                        try:
                            result = func(temp_path)
                            assert result == "test content", f"{func_name} didn't execute correctly"
                        finally:
                            os.unlink(temp_path)
                    
                    elif func_name == 'risky_divide':
                        result = func(10.0, 2.0)
                        abs(result - 5.0) < 1e-10
                    
                    elif func_name == 'complex_list_operation':
                        result = func([1, 2, 3, 4, 5])
                        assert result == [1, 3, 5], f"{func_name} didn't execute correctly"
                    
                except Exception as e:
                    # Some deprecated functions might fail, but should still warn
                    pass
                
                # Check that deprecation warning was issued
                assert len(w) > 0, f"No warning generated for deprecated function {func_name}"
                
                # Check that it's a DeprecationWarning
                deprecation_warnings = [warning for warning in w if issubclass(warning.category, DeprecationWarning)]
                assert len(deprecation_warnings) > 0, f"No DeprecationWarning generated for {func_name}"
                
                # Check warning message contains function name
                warning_message = str(deprecation_warnings[0].message)
                assert func_name in warning_message or "устарела" in warning_message, \
                    f"Warning message doesn't indicate deprecation: {warning_message}"
    
    @given(
        reason=st.text(min_size=10, max_size=100),
        alternative=st.one_of(st.none(), st.text(min_size=5, max_size=50)),
        removal_version=st.one_of(st.none(), st.text(min_size=3, max_size=10))
    )
    def test_deprecated_decorator_generates_warnings(self, reason, alternative, removal_version):
        """Test that the @deprecated decorator generates appropriate warnings"""
        
        # Create a test function with the deprecated decorator
        @deprecated(reason=reason, alternative=alternative, removal_version=removal_version)
        def test_function(x):
            return x * 2
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            # Call the decorated function
            result = test_function(5)
            
            # Function should still work correctly
            assert result == 10, "Deprecated function didn't execute correctly"
            
            # Should generate exactly one warning
            assert len(w) == 1, f"Expected 1 warning, got {len(w)}"
            
            # Should be a DeprecationWarning
            assert issubclass(w[0].category, DeprecationWarning), \
                f"Expected DeprecationWarning, got {w[0].category}"
            
            # Warning message should contain key information
            warning_message = str(w[0].message)
            assert "test_function" in warning_message, "Warning should contain function name"
            assert "устарела" in warning_message, "Warning should indicate deprecation in Russian"
            
            if alternative:
                assert alternative in warning_message, "Warning should contain alternative suggestion"
            
            if removal_version:
                assert removal_version in warning_message, "Warning should contain removal version"
    
    def test_deprecation_info_retrieval(self):
        """Test that deprecation information can be retrieved from decorated functions"""
        deprecated_funcs = list_deprecated_functions(legacy_module)
        
        for func_name in deprecated_funcs:
            func = getattr(legacy_module, func_name)
            info = show_deprecation_info(func)
            
            # Should return non-empty info for deprecated functions
            assert isinstance(info, dict), f"Deprecation info should be a dict for {func_name}"
            assert len(info) > 0, f"Deprecation info should not be empty for {func_name}"
            
            # Should contain expected keys
            expected_keys = ['reason', 'alternative', 'removal_version']
            for key in expected_keys:
                assert key in info, f"Missing key '{key}' in deprecation info for {func_name}"
    
    def test_non_deprecated_functions_no_warnings(self):
        """Test that non-deprecated functions don't generate warnings"""
        # Test some retained functions that should not be deprecated
        from fishertools.legacy import read_json, write_json, clean_string
        
        non_deprecated_funcs = [read_json, write_json, clean_string]
        
        for func in non_deprecated_funcs:
            info = show_deprecation_info(func)
            assert len(info) == 0, f"Non-deprecated function {func.__name__} has deprecation info"
    
    @given(
        a=st.floats(min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False),
        b=st.floats(min_value=0.1, max_value=1000, allow_nan=False, allow_infinity=False)  # Avoid division by zero
    )
    def test_risky_divide_warning_and_execution(self, a, b):
        """Test that risky_divide generates warning but still performs division"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            result = risky_divide(a, b)
            
            # Should generate deprecation warning
            assert len(w) > 0, "risky_divide should generate a warning"
            assert any(issubclass(warning.category, DeprecationWarning) for warning in w), \
                "Should generate DeprecationWarning"
            
            # Should still perform the calculation correctly
            expected = a / b
            assert abs(result - expected) < 1e-10, f"Expected {expected}, got {result}"
    
    @given(
        lst=st.lists(st.one_of(st.integers(), st.none()), min_size=0, max_size=20)
    )
    def test_complex_list_operation_warning_and_execution(self, lst):
        """Test that complex_list_operation generates warning but still works"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            result = complex_list_operation(lst)
            
            # Should generate deprecation warning
            assert len(w) > 0, "complex_list_operation should generate a warning"
            assert any(issubclass(warning.category, DeprecationWarning) for warning in w), \
                "Should generate DeprecationWarning"
            
            # Should still perform the operation correctly
            expected = [x for i, x in enumerate(lst) if i % 2 == 0 and x is not None]
            assert result == expected, f"Expected {expected}, got {result}"
    
    def test_warning_message_contains_migration_guidance(self):
        """Test that deprecation warnings contain helpful migration guidance"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            # Call a deprecated function
            risky_divide(10, 2)
            
            # Check warning message content
            assert len(w) > 0, "Should generate warning"
            warning_message = str(w[0].message)
            
            # Should contain migration guidance
            assert "safe_divide" in warning_message, "Should suggest safe alternative"
            assert "1.0.0" in warning_message, "Should mention removal version"
            assert "migration" in warning_message.lower(), "Should mention migration guide"