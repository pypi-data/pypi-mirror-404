"""
Property-based tests for backward compatibility

Feature: fishertools-refactor, Property 1: Backward Compatibility Preservation
For any retained function from the legacy library, calling it with the same inputs 
should produce the same outputs as in the previous version.

**Validates: Requirements 1.4**
"""

import pytest
from hypothesis import given, strategies as st, assume
import json
import tempfile
import os
from pathlib import Path

# Import both original and legacy versions for comparison
import fishertools.utils as original_utils
import fishertools.helpers as original_helpers  
import fishertools.decorators as original_decorators
import fishertools.legacy as legacy


class TestBackwardCompatibilityPreservation:
    """
    Property 1: Backward Compatibility Preservation
    For any retained function from the legacy library, calling it with the same inputs
    should produce the same outputs as in the previous version
    """
    
    @given(
        data=st.dictionaries(
            st.text(min_size=1, max_size=10), 
            st.one_of(st.text(), st.integers(), st.floats(allow_nan=False))
        ),
        indent=st.integers(min_value=0, max_value=8)
    )
    def test_json_operations_compatibility(self, data, indent):
        """Test that JSON read/write operations maintain identical behavior"""
        assume(len(data) > 0)  # Ensure we have some data
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            # Test write_json compatibility
            original_utils.write_json(data, temp_path, indent)
            with open(temp_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Clear file and write with legacy version
            os.remove(temp_path)
            legacy.write_json(data, temp_path, indent)
            with open(temp_path, 'r', encoding='utf-8') as f:
                legacy_content = f.read()
            
            assert original_content == legacy_content, "write_json output differs"
            
            # Test read_json compatibility
            original_result = original_utils.read_json(temp_path)
            legacy_result = legacy.read_json(temp_path)
            
            assert original_result == legacy_result, "read_json output differs"
            
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    @given(st.text(min_size=1, max_size=100))
    def test_string_operations_compatibility(self, text):
        """Test that string operations maintain identical behavior"""
        # Test clean_string
        original_cleaned = original_helpers.clean_string(text)
        legacy_cleaned = legacy.clean_string(text)
        assert original_cleaned == legacy_cleaned, "clean_string output differs"
        
        # Test validate_email (if text looks like email)
        if '@' in text and '.' in text:
            original_valid = original_helpers.validate_email(text)
            legacy_valid = legacy.validate_email(text)
            assert original_valid == legacy_valid, "validate_email output differs"
    
    @given(
        text=st.text(min_size=1, max_size=50),
        algorithm=st.sampled_from(['md5', 'sha1', 'sha256', 'sha512'])
    )
    def test_hash_string_compatibility(self, text, algorithm):
        """Test that hash_string maintains identical behavior"""
        original_hash = original_helpers.hash_string(text, algorithm)
        legacy_hash = legacy.hash_string(text, algorithm)
        assert original_hash == legacy_hash, "hash_string output differs"
    
    @given(
        length=st.integers(min_value=1, max_value=50),
        include_symbols=st.booleans()
    )
    def test_generate_password_compatibility(self, length, include_symbols):
        """Test that generate_password maintains identical character sets"""
        # We can't test exact output since it's random, but we can test properties
        original_pwd = original_helpers.generate_password(length, include_symbols)
        legacy_pwd = legacy.generate_password(length, include_symbols)
        
        # Both should have same length
        assert len(original_pwd) == len(legacy_pwd) == length
        
        # Both should use same character sets
        import string
        expected_chars = string.ascii_letters + string.digits
        if include_symbols:
            expected_chars += "!@#$%^&*"
        
        for char in original_pwd:
            assert char in expected_chars, f"Original password contains unexpected char: {char}"
        
        for char in legacy_pwd:
            assert char in expected_chars, f"Legacy password contains unexpected char: {char}"
    
    @given(
        lst=st.lists(st.integers(), min_size=1, max_size=20),
        chunk_size=st.integers(min_value=1, max_value=10)
    )
    def test_chunk_list_compatibility(self, lst, chunk_size):
        """Test that chunk_list maintains identical behavior"""
        original_chunks = original_helpers.chunk_list(lst, chunk_size)
        legacy_chunks = legacy.chunk_list(lst, chunk_size)
        assert original_chunks == legacy_chunks, "chunk_list output differs"
    
    @given(
        dicts=st.lists(
            st.dictionaries(st.text(min_size=1, max_size=5), st.integers()),
            min_size=1, max_size=5
        )
    )
    def test_merge_dicts_compatibility(self, dicts):
        """Test that merge_dicts maintains identical behavior"""
        original_merged = original_helpers.merge_dicts(*dicts)
        legacy_merged = legacy.merge_dicts(*dicts)
        assert original_merged == legacy_merged, "merge_dicts output differs"
    
    @given(
        nested_dict=st.dictionaries(
            st.text(min_size=1, max_size=5),
            st.one_of(
                st.integers(),
                st.dictionaries(st.text(min_size=1, max_size=3), st.integers())
            )
        ),
        sep=st.sampled_from(['.', '_', '-'])
    )
    def test_flatten_dict_compatibility(self, nested_dict, sep):
        """Test that flatten_dict maintains identical behavior"""
        assume(len(nested_dict) > 0)
        
        original_flat = original_utils.flatten_dict(nested_dict, sep=sep)
        legacy_flat = legacy.flatten_dict(nested_dict, sep=sep)
        assert original_flat == legacy_flat, "flatten_dict output differs"
    
    def test_timestamp_compatibility(self):
        """Test that timestamp format is identical"""
        # Since timestamp uses current time, we test format compatibility
        import time
        
        # Mock time to ensure identical output
        fixed_time = 1640995200.0  # 2022-01-01 00:00:00
        original_time_strftime = time.strftime
        
        def mock_strftime(fmt):
            return original_time_strftime(fmt, time.gmtime(fixed_time))
        
        time.strftime = mock_strftime
        
        try:
            # Import fresh to get mocked time
            import importlib
            importlib.reload(original_utils)
            from fishertools.legacy.deprecated import timestamp as legacy_timestamp
            
            original_ts = original_utils.timestamp()
            legacy_ts = legacy_timestamp()
            assert original_ts == legacy_ts, "timestamp format differs"
        finally:
            time.strftime = original_time_strftime
    
    @given(
        config_data=st.dictionaries(
            st.text(min_size=1, max_size=5),
            st.one_of(
                st.integers(),
                st.text(),
                st.dictionaries(st.text(min_size=1, max_size=3), st.integers())
            )
        ),
        key=st.text(min_size=1, max_size=10),
        default_value=st.one_of(st.none(), st.integers(), st.text())
    )
    def test_quick_config_compatibility(self, config_data, key, default_value):
        """Test that QuickConfig maintains identical behavior"""
        assume(len(config_data) > 0)
        
        original_config = original_helpers.QuickConfig(config_data)
        legacy_config = legacy.QuickConfig(config_data)
        
        # Test get method
        original_result = original_config.get(key, default_value)
        legacy_result = legacy_config.get(key, default_value)
        assert original_result == legacy_result, "QuickConfig.get output differs"
        
        # Test to_dict method
        assert original_config.to_dict() == legacy_config.to_dict(), "QuickConfig.to_dict output differs"
    
    def test_simple_logger_compatibility(self):
        """Test that SimpleLogger maintains identical behavior"""
        import io
        import sys
        from contextlib import redirect_stdout
        
        # Capture output from both loggers
        original_logger = original_helpers.SimpleLogger("Test")
        legacy_logger = legacy.SimpleLogger("Test")
        
        test_message = "Test message"
        
        # Test each log level
        for method_name in ['info', 'warning', 'error', 'debug']:
            original_output = io.StringIO()
            legacy_output = io.StringIO()
            
            with redirect_stdout(original_output):
                getattr(original_logger, method_name)(test_message)
            
            with redirect_stdout(legacy_output):
                getattr(legacy_logger, method_name)(test_message)
            
            assert original_output.getvalue() == legacy_output.getvalue(), \
                f"SimpleLogger.{method_name} output differs"