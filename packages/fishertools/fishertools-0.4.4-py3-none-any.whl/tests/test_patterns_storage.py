"""
Property-based tests for the JSONStorage class in fishertools.patterns.

Tests the correctness properties of the JSONStorage class using hypothesis
for property-based testing.

**Validates: Requirements 9.2, 9.3, 9.4**
"""

import pytest
import json
import os
import tempfile
import shutil
from pathlib import Path
from hypothesis import given, strategies as st, assume

from fishertools.patterns.storage import JSONStorage


class TestJSONStorageRoundTrip:
    """
    Property 4: JSONStorage Round Trip
    
    For any valid Python dictionary, saving it with JSONStorage and then
    loading it should return an equivalent dictionary.
    
    **Validates: Requirements 9.2, 9.3**
    """
    
    def test_round_trip_simple_dict(self):
        """Test round trip with a simple dictionary."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JSONStorage(os.path.join(tmpdir, "test.json"))
            data = {"name": "Alice", "age": 30}
            
            storage.save(data)
            loaded = storage.load()
            
            assert loaded == data
    
    def test_round_trip_nested_dict(self):
        """Test round trip with nested dictionaries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JSONStorage(os.path.join(tmpdir, "test.json"))
            data = {
                "user": {
                    "name": "Bob",
                    "address": {
                        "city": "New York",
                        "zip": "10001"
                    }
                },
                "active": True
            }
            
            storage.save(data)
            loaded = storage.load()
            
            assert loaded == data
    
    def test_round_trip_with_lists(self):
        """Test round trip with lists in dictionary."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JSONStorage(os.path.join(tmpdir, "test.json"))
            data = {
                "items": [1, 2, 3, 4, 5],
                "names": ["Alice", "Bob", "Charlie"]
            }
            
            storage.save(data)
            loaded = storage.load()
            
            assert loaded == data
    
    def test_round_trip_with_various_types(self):
        """Test round trip with various JSON-compatible types."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JSONStorage(os.path.join(tmpdir, "test.json"))
            data = {
                "string": "hello",
                "integer": 42,
                "float": 3.14,
                "boolean": True,
                "null": None,
                "list": [1, "two", 3.0, False, None],
                "nested": {"key": "value"}
            }
            
            storage.save(data)
            loaded = storage.load()
            
            assert loaded == data
    
    def test_round_trip_empty_dict(self):
        """Test round trip with empty dictionary."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JSONStorage(os.path.join(tmpdir, "test.json"))
            data = {}
            
            storage.save(data)
            loaded = storage.load()
            
            assert loaded == data
    
    def test_round_trip_multiple_saves(self):
        """Test that multiple saves overwrite previous data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JSONStorage(os.path.join(tmpdir, "test.json"))
            
            # First save
            data1 = {"version": 1}
            storage.save(data1)
            
            # Second save
            data2 = {"version": 2, "updated": True}
            storage.save(data2)
            
            loaded = storage.load()
            assert loaded == data2
    
    def test_round_trip_with_unicode(self):
        """Test round trip with unicode characters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JSONStorage(os.path.join(tmpdir, "test.json"))
            data = {
                "greeting": "Hello 世界",
                "emoji": "🎉",
                "accents": "café"
            }
            
            storage.save(data)
            loaded = storage.load()
            
            assert loaded == data
    
    def test_round_trip_with_special_strings(self):
        """Test round trip with special string characters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JSONStorage(os.path.join(tmpdir, "test.json"))
            data = {
                "newline": "line1\nline2",
                "tab": "col1\tcol2",
                "quote": 'He said "hello"',
                "backslash": "path\\to\\file"
            }
            
            storage.save(data)
            loaded = storage.load()
            
            assert loaded == data
    
    @given(st.dictionaries(
        st.text(min_size=1),
        st.one_of(
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.text(),
            st.booleans(),
            st.none()
        ),
        min_size=0,
        max_size=10
    ))
    def test_round_trip_property(self, data):
        """
        Property: For any valid Python dictionary with JSON-serializable values,
        saving and loading should return an equivalent dictionary.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JSONStorage(os.path.join(tmpdir, "test.json"))
            
            storage.save(data)
            loaded = storage.load()
            
            assert loaded == data


class TestJSONStorageCreatesDirectories:
    """
    Property 5: JSONStorage Creates Directories
    
    For any file path with non-existent parent directories, JSONStorage should
    create all necessary directories when saving data.
    
    **Validates: Requirements 9.4**
    """
    
    def test_creates_single_directory(self):
        """Test that JSONStorage creates a single parent directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "subdir", "test.json")
            storage = JSONStorage(file_path)
            
            # Directory should not exist yet
            assert not os.path.exists(os.path.dirname(file_path))
            
            # Save should create the directory
            storage.save({"data": "test"})
            
            # Directory should now exist
            assert os.path.exists(os.path.dirname(file_path))
            assert os.path.isdir(os.path.dirname(file_path))
    
    def test_creates_nested_directories(self):
        """Test that JSONStorage creates nested parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "level1", "level2", "level3", "test.json")
            storage = JSONStorage(file_path)
            
            # Directories should not exist yet
            assert not os.path.exists(os.path.dirname(file_path))
            
            # Save should create all directories
            storage.save({"data": "test"})
            
            # All directories should now exist
            assert os.path.exists(os.path.dirname(file_path))
            assert os.path.isdir(os.path.dirname(file_path))
    
    def test_creates_directories_with_special_names(self):
        """Test that JSONStorage creates directories with special characters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "dir-with-dash", "dir_with_underscore", "test.json")
            storage = JSONStorage(file_path)
            
            storage.save({"data": "test"})
            
            assert os.path.exists(os.path.dirname(file_path))
    
    def test_does_not_fail_if_directory_exists(self):
        """Test that JSONStorage doesn't fail if directory already exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = os.path.join(tmpdir, "existing")
            os.makedirs(subdir)
            
            file_path = os.path.join(subdir, "test.json")
            storage = JSONStorage(file_path)
            
            # Should not raise an exception
            storage.save({"data": "test"})
            
            assert os.path.exists(file_path)
    
    def test_creates_directories_for_deeply_nested_paths(self):
        """Test that JSONStorage creates directories for deeply nested paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a deeply nested path
            nested_path = os.path.join(tmpdir, *[f"level{i}" for i in range(10)])
            file_path = os.path.join(nested_path, "test.json")
            
            storage = JSONStorage(file_path)
            storage.save({"data": "test"})
            
            assert os.path.exists(file_path)
            assert os.path.isfile(file_path)
    
    @given(st.lists(st.text(
        alphabet="abcdefghijklmnopqrstuvwxyz0123456789_-",
        min_size=1,
        max_size=20
    ), min_size=1, max_size=5))
    def test_creates_directories_property(self, path_parts):
        """
        Property: For any valid path with non-existent parent directories,
        JSONStorage should create all necessary directories when saving.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Build a nested path
            nested_path = os.path.join(tmpdir, *path_parts)
            file_path = os.path.join(nested_path, "test.json")
            
            storage = JSONStorage(file_path)
            storage.save({"test": "data"})
            
            # File should exist
            assert os.path.exists(file_path)
            # All parent directories should exist
            assert os.path.isdir(os.path.dirname(file_path))


class TestJSONStorageFileOperations:
    """Test basic file operations of JSONStorage."""
    
    def test_exists_returns_false_for_nonexistent_file(self):
        """Test that exists() returns False for non-existent file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JSONStorage(os.path.join(tmpdir, "nonexistent.json"))
            assert storage.exists() is False
    
    def test_exists_returns_true_after_save(self):
        """Test that exists() returns True after saving."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test.json")
            storage = JSONStorage(file_path)
            
            storage.save({"data": "test"})
            assert storage.exists() is True
    
    def test_load_returns_empty_dict_for_nonexistent_file(self):
        """Test that load() returns empty dict for non-existent file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JSONStorage(os.path.join(tmpdir, "nonexistent.json"))
            loaded = storage.load()
            
            assert loaded == {}
    
    def test_save_creates_file(self):
        """Test that save() creates the file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test.json")
            storage = JSONStorage(file_path)
            
            assert not os.path.exists(file_path)
            storage.save({"data": "test"})
            assert os.path.exists(file_path)
    
    def test_save_writes_valid_json(self):
        """Test that save() writes valid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test.json")
            storage = JSONStorage(file_path)
            
            data = {"key": "value", "number": 42}
            storage.save(data)
            
            # Read file directly and parse JSON
            with open(file_path, 'r') as f:
                loaded = json.load(f)
            
            assert loaded == data
    
    def test_file_path_attribute(self):
        """Test that file_path attribute is set correctly."""
        file_path = "test/path/file.json"
        storage = JSONStorage(file_path)
        
        assert storage.file_path == file_path


class TestJSONStorageErrorHandling:
    """Test error handling in JSONStorage."""
    
    def test_save_raises_typeerror_for_non_serializable_data(self):
        """Test that save() raises TypeError for non-JSON-serializable data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JSONStorage(os.path.join(tmpdir, "test.json"))
            
            # Try to save a non-serializable object
            with pytest.raises(TypeError):
                storage.save({"obj": object()})
    
    def test_save_raises_typeerror_for_set(self):
        """Test that save() raises TypeError for sets."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JSONStorage(os.path.join(tmpdir, "test.json"))
            
            with pytest.raises(TypeError):
                storage.save({"items": {1, 2, 3}})
    
    def test_load_raises_error_for_corrupted_json(self):
        """Test that load() raises error for corrupted JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test.json")
            
            # Write invalid JSON
            with open(file_path, 'w') as f:
                f.write("{invalid json}")
            
            storage = JSONStorage(file_path)
            
            with pytest.raises(json.JSONDecodeError):
                storage.load()


class TestJSONStorageIntegration:
    """Integration tests for JSONStorage."""
    
    def test_multiple_storage_instances_same_file(self):
        """Test that multiple storage instances can access the same file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "shared.json")
            
            storage1 = JSONStorage(file_path)
            storage1.save({"version": 1})
            
            storage2 = JSONStorage(file_path)
            loaded = storage2.load()
            
            assert loaded == {"version": 1}
    
    def test_storage_with_relative_path(self):
        """Test that JSONStorage works with relative paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Change to temp directory
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                
                storage = JSONStorage("test.json")
                storage.save({"data": "test"})
                
                assert os.path.exists("test.json")
                loaded = storage.load()
                assert loaded == {"data": "test"}
            finally:
                os.chdir(original_cwd)
    
    def test_storage_with_absolute_path(self):
        """Test that JSONStorage works with absolute paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.abspath(os.path.join(tmpdir, "test.json"))
            storage = JSONStorage(file_path)
            
            storage.save({"data": "test"})
            loaded = storage.load()
            
            assert loaded == {"data": "test"}
    
    def test_storage_preserves_data_types(self):
        """Test that JSONStorage preserves data types correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JSONStorage(os.path.join(tmpdir, "test.json"))
            
            data = {
                "int": 42,
                "float": 3.14,
                "string": "hello",
                "bool_true": True,
                "bool_false": False,
                "null": None,
                "list": [1, 2, 3],
                "nested": {"key": "value"}
            }
            
            storage.save(data)
            loaded = storage.load()
            
            # Verify types are preserved
            assert isinstance(loaded["int"], int)
            assert isinstance(loaded["float"], float)
            assert isinstance(loaded["string"], str)
            assert isinstance(loaded["bool_true"], bool)
            assert isinstance(loaded["bool_false"], bool)
            assert loaded["null"] is None
            assert isinstance(loaded["list"], list)
            assert isinstance(loaded["nested"], dict)
