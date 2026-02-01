"""
Unit tests for exception type identification module.

Tests the exception type identification functionality including:
- Identifying exception types from exception objects
- Getting exception type information
- Checking if exception types are supported
- Retrieving exception type mappings
"""

import pytest
from fishertools.errors.exception_types import (
    identify_exception_type,
    get_exception_type_info,
    is_supported_exception_type,
    get_exception_type_mapping,
    get_supported_exception_types,
    ExceptionTypeInfo,
    EXCEPTION_TYPE_MAPPING
)


class TestIdentifyExceptionType:
    """Tests for identify_exception_type function."""
    
    def test_identify_type_error(self):
        """Test identifying TypeError."""
        exc = TypeError("unsupported operand type")
        assert identify_exception_type(exc) == "TypeError"
    
    def test_identify_value_error(self):
        """Test identifying ValueError."""
        exc = ValueError("invalid literal for int()")
        assert identify_exception_type(exc) == "ValueError"
    
    def test_identify_index_error(self):
        """Test identifying IndexError."""
        exc = IndexError("list index out of range")
        assert identify_exception_type(exc) == "IndexError"
    
    def test_identify_key_error(self):
        """Test identifying KeyError."""
        exc = KeyError("missing_key")
        assert identify_exception_type(exc) == "KeyError"
    
    def test_identify_attribute_error(self):
        """Test identifying AttributeError."""
        exc = AttributeError("'str' object has no attribute 'append'")
        assert identify_exception_type(exc) == "AttributeError"
    
    def test_identify_file_not_found_error(self):
        """Test identifying FileNotFoundError."""
        exc = FileNotFoundError("No such file or directory")
        assert identify_exception_type(exc) == "FileNotFoundError"
    
    def test_identify_permission_error(self):
        """Test identifying PermissionError."""
        exc = PermissionError("Permission denied")
        assert identify_exception_type(exc) == "PermissionError"
    
    def test_identify_zero_division_error(self):
        """Test identifying ZeroDivisionError."""
        exc = ZeroDivisionError("division by zero")
        assert identify_exception_type(exc) == "ZeroDivisionError"
    
    def test_identify_name_error(self):
        """Test identifying NameError."""
        exc = NameError("name 'undefined_var' is not defined")
        assert identify_exception_type(exc) == "NameError"
    
    def test_identify_unknown_exception(self):
        """Test identifying unknown exception type."""
        class CustomException(Exception):
            pass
        
        exc = CustomException("custom error")
        assert identify_exception_type(exc) == "CustomException"
    
    def test_identify_with_non_exception_raises_type_error(self):
        """Test that non-Exception objects raise TypeError."""
        with pytest.raises(TypeError):
            identify_exception_type("not an exception")
        
        with pytest.raises(TypeError):
            identify_exception_type(42)
        
        with pytest.raises(TypeError):
            identify_exception_type(None)
    
    def test_identify_with_exception_subclass(self):
        """Test identifying exception subclasses."""
        # FileNotFoundError is a subclass of OSError
        exc = FileNotFoundError("file not found")
        assert identify_exception_type(exc) == "FileNotFoundError"


class TestGetExceptionTypeInfo:
    """Tests for get_exception_type_info function."""
    
    def test_get_info_type_error(self):
        """Test getting info for TypeError."""
        exc = TypeError("unsupported operand type")
        info = get_exception_type_info(exc)
        
        assert isinstance(info, ExceptionTypeInfo)
        assert info.name == "TypeError"
        assert info.exception_class == TypeError
        assert "Type mismatch" in info.description
        assert len(info.common_causes) > 0
    
    def test_get_info_value_error(self):
        """Test getting info for ValueError."""
        exc = ValueError("invalid literal")
        info = get_exception_type_info(exc)
        
        assert info.name == "ValueError"
        assert info.exception_class == ValueError
        assert "Invalid value" in info.description
    
    def test_get_info_index_error(self):
        """Test getting info for IndexError."""
        exc = IndexError("list index out of range")
        info = get_exception_type_info(exc)
        
        assert info.name == "IndexError"
        assert "Sequence index" in info.description
    
    def test_get_info_key_error(self):
        """Test getting info for KeyError."""
        exc = KeyError("missing_key")
        info = get_exception_type_info(exc)
        
        assert info.name == "KeyError"
        assert "Dictionary key" in info.description
    
    def test_get_info_attribute_error(self):
        """Test getting info for AttributeError."""
        exc = AttributeError("'str' object has no attribute 'append'")
        info = get_exception_type_info(exc)
        
        assert info.name == "AttributeError"
        assert "Attribute or method" in info.description
    
    def test_get_info_file_not_found_error(self):
        """Test getting info for FileNotFoundError."""
        exc = FileNotFoundError("No such file")
        info = get_exception_type_info(exc)
        
        assert info.name == "FileNotFoundError"
        assert "File or directory" in info.description
    
    def test_get_info_permission_error(self):
        """Test getting info for PermissionError."""
        exc = PermissionError("Permission denied")
        info = get_exception_type_info(exc)
        
        assert info.name == "PermissionError"
        assert "Permission denied" in info.description
    
    def test_get_info_zero_division_error(self):
        """Test getting info for ZeroDivisionError."""
        exc = ZeroDivisionError("division by zero")
        info = get_exception_type_info(exc)
        
        assert info.name == "ZeroDivisionError"
        assert "Division by zero" in info.description
    
    def test_get_info_name_error(self):
        """Test getting info for NameError."""
        exc = NameError("name 'x' is not defined")
        info = get_exception_type_info(exc)
        
        assert info.name == "NameError"
        assert "Name not defined" in info.description
    
    def test_get_info_unknown_exception(self):
        """Test getting info for unknown exception type."""
        class CustomException(Exception):
            pass
        
        exc = CustomException("custom error")
        info = get_exception_type_info(exc)
        
        assert info.name == "CustomException"
        assert info.exception_class == CustomException
        assert "unexpected error" in info.description.lower()
    
    def test_get_info_with_non_exception_raises_type_error(self):
        """Test that non-Exception objects raise TypeError."""
        with pytest.raises(TypeError):
            get_exception_type_info("not an exception")
        
        with pytest.raises(TypeError):
            get_exception_type_info(42)
    
    def test_info_has_common_causes(self):
        """Test that exception info includes common causes."""
        exc = TypeError("unsupported operand type")
        info = get_exception_type_info(exc)
        
        assert isinstance(info.common_causes, list)
        assert len(info.common_causes) > 0
        assert all(isinstance(cause, str) for cause in info.common_causes)


class TestIsSupportedExceptionType:
    """Tests for is_supported_exception_type function."""
    
    def test_supported_type_error(self):
        """Test that TypeError is supported."""
        exc = TypeError("unsupported operand type")
        assert is_supported_exception_type(exc) is True
    
    def test_supported_value_error(self):
        """Test that ValueError is supported."""
        exc = ValueError("invalid literal")
        assert is_supported_exception_type(exc) is True
    
    def test_supported_index_error(self):
        """Test that IndexError is supported."""
        exc = IndexError("list index out of range")
        assert is_supported_exception_type(exc) is True
    
    def test_supported_key_error(self):
        """Test that KeyError is supported."""
        exc = KeyError("missing_key")
        assert is_supported_exception_type(exc) is True
    
    def test_supported_attribute_error(self):
        """Test that AttributeError is supported."""
        exc = AttributeError("'str' object has no attribute 'append'")
        assert is_supported_exception_type(exc) is True
    
    def test_supported_file_not_found_error(self):
        """Test that FileNotFoundError is supported."""
        exc = FileNotFoundError("No such file")
        assert is_supported_exception_type(exc) is True
    
    def test_supported_permission_error(self):
        """Test that PermissionError is supported."""
        exc = PermissionError("Permission denied")
        assert is_supported_exception_type(exc) is True
    
    def test_supported_zero_division_error(self):
        """Test that ZeroDivisionError is supported."""
        exc = ZeroDivisionError("division by zero")
        assert is_supported_exception_type(exc) is True
    
    def test_supported_name_error(self):
        """Test that NameError is supported."""
        exc = NameError("name 'x' is not defined")
        assert is_supported_exception_type(exc) is True
    
    def test_unsupported_custom_exception(self):
        """Test that custom exceptions are not supported."""
        class CustomException(Exception):
            pass
        
        exc = CustomException("custom error")
        assert is_supported_exception_type(exc) is False
    
    def test_unsupported_runtime_error(self):
        """Test that RuntimeError is not in supported list."""
        exc = RuntimeError("runtime error")
        assert is_supported_exception_type(exc) is False
    
    def test_is_supported_with_non_exception_raises_type_error(self):
        """Test that non-Exception objects raise TypeError."""
        with pytest.raises(TypeError):
            is_supported_exception_type("not an exception")
        
        with pytest.raises(TypeError):
            is_supported_exception_type(42)


class TestGetExceptionTypeMapping:
    """Tests for get_exception_type_mapping function."""
    
    def test_mapping_is_dict(self):
        """Test that mapping returns a dictionary."""
        mapping = get_exception_type_mapping()
        assert isinstance(mapping, dict)
    
    def test_mapping_contains_all_supported_types(self):
        """Test that mapping contains all supported exception types."""
        mapping = get_exception_type_mapping()
        
        expected_types = [
            TypeError, ValueError, IndexError, KeyError, AttributeError,
            FileNotFoundError, PermissionError, ZeroDivisionError, NameError
        ]
        
        for exc_type in expected_types:
            assert exc_type in mapping
    
    def test_mapping_values_are_exception_type_info(self):
        """Test that all mapping values are ExceptionTypeInfo instances."""
        mapping = get_exception_type_mapping()
        
        for exc_type, info in mapping.items():
            assert isinstance(info, ExceptionTypeInfo)
            assert info.exception_class == exc_type
    
    def test_mapping_is_copy(self):
        """Test that returned mapping is a copy, not the original."""
        mapping1 = get_exception_type_mapping()
        mapping2 = get_exception_type_mapping()
        
        # Should be equal but not the same object
        assert mapping1 == mapping2
        assert mapping1 is not mapping2
    
    def test_mapping_has_correct_structure(self):
        """Test that mapping entries have correct structure."""
        mapping = get_exception_type_mapping()
        
        for exc_type, info in mapping.items():
            assert hasattr(info, 'exception_class')
            assert hasattr(info, 'name')
            assert hasattr(info, 'description')
            assert hasattr(info, 'common_causes')
            
            assert isinstance(info.name, str)
            assert isinstance(info.description, str)
            assert isinstance(info.common_causes, list)


class TestGetSupportedExceptionTypes:
    """Tests for get_supported_exception_types function."""
    
    def test_returns_list(self):
        """Test that function returns a list."""
        types = get_supported_exception_types()
        assert isinstance(types, list)
    
    def test_contains_all_supported_types(self):
        """Test that list contains all supported exception type names."""
        types = get_supported_exception_types()
        
        expected_names = [
            "TypeError", "ValueError", "IndexError", "KeyError", "AttributeError",
            "FileNotFoundError", "PermissionError", "ZeroDivisionError", "NameError"
        ]
        
        for name in expected_names:
            assert name in types
    
    def test_all_items_are_strings(self):
        """Test that all items in the list are strings."""
        types = get_supported_exception_types()
        assert all(isinstance(t, str) for t in types)
    
    def test_no_duplicates(self):
        """Test that there are no duplicate exception type names."""
        types = get_supported_exception_types()
        assert len(types) == len(set(types))
    
    def test_correct_count(self):
        """Test that the list has the correct number of supported types."""
        types = get_supported_exception_types()
        # Should have 9 supported exception types
        assert len(types) == 9


class TestExceptionTypeMapping:
    """Tests for the EXCEPTION_TYPE_MAPPING constant."""
    
    def test_mapping_exists(self):
        """Test that EXCEPTION_TYPE_MAPPING is defined."""
        assert EXCEPTION_TYPE_MAPPING is not None
        assert isinstance(EXCEPTION_TYPE_MAPPING, dict)
    
    def test_mapping_has_all_types(self):
        """Test that mapping has all expected exception types."""
        expected_types = [
            TypeError, ValueError, IndexError, KeyError, AttributeError,
            FileNotFoundError, PermissionError, ZeroDivisionError, NameError
        ]
        
        for exc_type in expected_types:
            assert exc_type in EXCEPTION_TYPE_MAPPING
    
    def test_mapping_values_are_info_objects(self):
        """Test that all values are ExceptionTypeInfo objects."""
        for exc_type, info in EXCEPTION_TYPE_MAPPING.items():
            assert isinstance(info, ExceptionTypeInfo)
            assert info.exception_class == exc_type
            assert isinstance(info.name, str)
            assert isinstance(info.description, str)
            assert isinstance(info.common_causes, list)


class TestExceptionTypeIdentificationIntegration:
    """Integration tests for exception type identification."""
    
    def test_identify_and_get_info_consistency(self):
        """Test that identify_exception_type and get_exception_type_info are consistent."""
        exceptions = [
            TypeError("test"),
            ValueError("test"),
            IndexError("test"),
            KeyError("test"),
            AttributeError("test"),
            FileNotFoundError("test"),
            PermissionError("test"),
            ZeroDivisionError("test"),
            NameError("test"),
        ]
        
        for exc in exceptions:
            exc_type_name = identify_exception_type(exc)
            info = get_exception_type_info(exc)
            
            assert exc_type_name == info.name
    
    def test_supported_check_consistency(self):
        """Test that is_supported_exception_type is consistent with mapping."""
        mapping = get_exception_type_mapping()
        
        for exc_type in mapping.keys():
            exc = exc_type("test")
            assert is_supported_exception_type(exc) is True
    
    def test_all_supported_types_in_list(self):
        """Test that all supported types are in the supported types list."""
        supported_list = get_supported_exception_types()
        mapping = get_exception_type_mapping()
        
        for info in mapping.values():
            assert info.name in supported_list
    
    def test_exception_type_info_completeness(self):
        """Test that all exception type info objects are complete."""
        mapping = get_exception_type_mapping()
        
        for exc_type, info in mapping.items():
            # Check all required fields are present and non-empty
            assert info.exception_class is not None
            assert info.name and len(info.name) > 0
            assert info.description and len(info.description) > 0
            assert info.common_causes and len(info.common_causes) > 0
            
            # Check all common causes are non-empty strings
            for cause in info.common_causes:
                assert isinstance(cause, str)
                assert len(cause) > 0
