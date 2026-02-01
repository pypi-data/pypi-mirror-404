"""
Unit tests for safe file operations.
"""

import pytest
import tempfile
import os
from pathlib import Path
from fishertools.safe.files import (
    safe_read_file, safe_write_file, safe_file_exists, 
    safe_get_file_size, safe_list_files
)


class TestSafeFileOperations:
    """Unit tests for safe file operations."""
    
    def test_safe_read_file_existing_file(self):
        """Test reading an existing file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
            f.write("Test content")
            temp_path = f.name
        
        try:
            result = safe_read_file(temp_path)
            assert result == "Test content"
        finally:
            os.unlink(temp_path)
    
    def test_safe_read_file_nonexistent_file(self):
        """Test reading a non-existent file returns default."""
        result = safe_read_file("nonexistent_file.txt", default="default content")
        assert result == "default content"
    
    def test_safe_write_file_success(self):
        """Test writing to a file successfully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test_file.txt"
            result = safe_write_file(file_path, "Hello World")
            assert result is True
            assert file_path.exists()
            assert file_path.read_text(encoding='utf-8') == "Hello World"
    
    def test_safe_file_exists_existing_file(self):
        """Test checking existence of an existing file."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        
        try:
            assert safe_file_exists(temp_path) is True
        finally:
            os.unlink(temp_path)
    
    def test_safe_file_exists_nonexistent_file(self):
        """Test checking existence of a non-existent file."""
        assert safe_file_exists("nonexistent_file.txt") is False
    
    def test_safe_get_file_size_existing_file(self):
        """Test getting size of an existing file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
            f.write("12345")  # 5 bytes
            temp_path = f.name
        
        try:
            size = safe_get_file_size(temp_path)
            assert size == 5
        finally:
            os.unlink(temp_path)
    
    def test_safe_get_file_size_nonexistent_file(self):
        """Test getting size of a non-existent file returns default."""
        size = safe_get_file_size("nonexistent_file.txt", default=100)
        assert size == 100
    
    def test_safe_list_files_existing_directory(self):
        """Test listing files in an existing directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create some test files
            (Path(temp_dir) / "file1.txt").write_text("content1")
            (Path(temp_dir) / "file2.py").write_text("content2")
            (Path(temp_dir) / "subdir").mkdir()
            
            files = safe_list_files(temp_dir)
            assert "file1.txt" in files
            assert "file2.py" in files
            assert len(files) == 2  # Should not include subdirectory
    
    def test_safe_list_files_nonexistent_directory(self):
        """Test listing files in a non-existent directory returns default."""
        files = safe_list_files("nonexistent_directory", default=["default"])
        assert files == ["default"]
    
    def test_input_validation_errors(self):
        """Test that functions raise appropriate errors for invalid inputs."""
        from fishertools.errors.exceptions import SafeUtilityError
        
        with pytest.raises(SafeUtilityError, match="не может быть None"):
            safe_read_file(None)
        
        with pytest.raises(SafeUtilityError, match="должна быть строкой"):
            safe_read_file("test.txt", encoding=123)
        
        with pytest.raises(SafeUtilityError, match="должно быть строкой"):
            safe_write_file("test.txt", 123)



class TestProjectRoot:
    """Tests for project_root function."""
    
    def test_project_root_from_current_directory(self):
        """Test finding project root from current directory."""
        from fishertools.safe.files import project_root
        
        root = project_root()
        assert root is not None
        assert Path(root).exists()
        # Should find one of the markers
        markers = ['setup.py', 'pyproject.toml', '.git', '.gitignore']
        assert any((Path(root) / marker).exists() for marker in markers)
    
    def test_project_root_from_subdirectory(self):
        """Test finding project root from a subdirectory."""
        from fishertools.safe.files import project_root
        
        # Get root from current directory
        root1 = project_root()
        
        # Get root from a subdirectory
        subdir = Path(root1) / "fishertools"
        if subdir.exists():
            root2 = project_root(subdir)
            assert root1 == root2
    
    def test_project_root_not_found(self):
        """Test that RuntimeError is raised when project root cannot be found."""
        from fishertools.safe.files import project_root
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a temporary directory with no markers
            with pytest.raises(RuntimeError, match="Could not determine project root"):
                project_root(temp_dir)


class TestFindFile:
    """Tests for find_file function."""
    
    def test_find_file_existing_file(self):
        """Test finding an existing file."""
        from fishertools.safe.files import find_file
        
        # Find setup.py which should exist in project root
        path = find_file("setup.py")
        assert path is not None
        assert Path(path).exists()
        assert Path(path).name == "setup.py"
    
    def test_find_file_nonexistent_file(self):
        """Test finding a non-existent file returns None."""
        from fishertools.safe.files import find_file
        
        path = find_file("nonexistent_file_12345.txt")
        assert path is None
    
    def test_find_file_from_subdirectory(self):
        """Test finding a file starting from a subdirectory."""
        from fishertools.safe.files import find_file
        
        # Create a test file in a temporary subdirectory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            subdir = temp_path / "subdir"
            subdir.mkdir()
            
            # Create a test file in the subdirectory
            test_file = subdir / "test.txt"
            test_file.write_text("test content")
            
            # Find the file from the subdirectory
            path = find_file("test.txt", subdir)
            assert path is not None
            assert Path(path).exists()
            assert Path(path).name == "test.txt"


class TestSafeOpen:
    """Tests for safe_open function."""
    
    def test_safe_open_existing_file(self):
        """Test opening an existing file."""
        from fishertools.safe.files import safe_open
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
            f.write("Test content")
            temp_path = f.name
        
        try:
            with safe_open(temp_path) as f:
                content = f.read()
            assert content == "Test content"
        finally:
            os.unlink(temp_path)
    
    def test_safe_open_nonexistent_file(self):
        """Test opening a non-existent file raises FileNotFoundError."""
        from fishertools.safe.files import safe_open
        
        with pytest.raises(FileNotFoundError):
            safe_open("nonexistent_file_12345.txt")
    
    def test_safe_open_write_mode(self):
        """Test opening a file in write mode."""
        from fishertools.safe.files import safe_open
        
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test_file.txt"
            
            with safe_open(file_path, mode='w') as f:
                f.write("Hello World")
            
            assert file_path.exists()
            assert file_path.read_text(encoding='utf-8') == "Hello World"



# ============================================================================
# Tests for fishertools-file-utils spec functions
# ============================================================================

from hypothesis import given, strategies as st, settings
import hashlib


class TestEnsureDir:
    """Unit tests for ensure_dir function."""
    
    def test_ensure_dir_creates_new_directory(self):
        """Test creating a new directory."""
        from fishertools.safe.files import ensure_dir
        
        with tempfile.TemporaryDirectory() as temp_dir:
            new_dir = Path(temp_dir) / "new_directory"
            result = ensure_dir(new_dir)
            
            assert isinstance(result, Path)
            assert new_dir.exists()
            assert new_dir.is_dir()
    
    def test_ensure_dir_creates_nested_directories(self):
        """Test creating nested directories."""
        from fishertools.safe.files import ensure_dir
        
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_dir = Path(temp_dir) / "level1" / "level2" / "level3"
            result = ensure_dir(nested_dir)
            
            assert isinstance(result, Path)
            assert nested_dir.exists()
            assert nested_dir.is_dir()
    
    def test_ensure_dir_idempotent(self):
        """Test that ensure_dir is idempotent."""
        from fishertools.safe.files import ensure_dir
        
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir) / "test_dir"
            
            # First call
            result1 = ensure_dir(test_dir)
            assert test_dir.exists()
            
            # Second call should not raise error
            result2 = ensure_dir(test_dir)
            assert test_dir.exists()
            assert result1 == result2
    
    def test_ensure_dir_accepts_string_path(self):
        """Test that ensure_dir accepts string paths."""
        from fishertools.safe.files import ensure_dir
        
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = str(Path(temp_dir) / "test_dir")
            result = ensure_dir(test_dir)
            
            assert isinstance(result, Path)
            assert Path(test_dir).exists()
    
    def test_ensure_dir_accepts_path_object(self):
        """Test that ensure_dir accepts Path objects."""
        from fishertools.safe.files import ensure_dir
        
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir) / "test_dir"
            result = ensure_dir(test_dir)
            
            assert isinstance(result, Path)
            assert test_dir.exists()
    
    def test_ensure_dir_returns_path_object(self):
        """Test that ensure_dir returns a Path object."""
        from fishertools.safe.files import ensure_dir
        
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir) / "test_dir"
            result = ensure_dir(test_dir)
            
            assert isinstance(result, Path)
            assert result == test_dir


class TestGetFileHash:
    """Unit tests for get_file_hash function."""
    
    def test_get_file_hash_sha256_default(self):
        """Test computing SHA256 hash (default algorithm)."""
        from fishertools.safe.files import get_file_hash
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            result = get_file_hash(temp_path)
            # Verify it's a valid hex string
            assert isinstance(result, str)
            assert len(result) == 64  # SHA256 produces 64 hex characters
            assert all(c in '0123456789abcdef' for c in result)
        finally:
            os.unlink(temp_path)
    
    def test_get_file_hash_md5(self):
        """Test computing MD5 hash."""
        from fishertools.safe.files import get_file_hash
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            result = get_file_hash(temp_path, algorithm='md5')
            assert isinstance(result, str)
            assert len(result) == 32  # MD5 produces 32 hex characters
        finally:
            os.unlink(temp_path)
    
    def test_get_file_hash_sha1(self):
        """Test computing SHA1 hash."""
        from fishertools.safe.files import get_file_hash
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            result = get_file_hash(temp_path, algorithm='sha1')
            assert isinstance(result, str)
            assert len(result) == 40  # SHA1 produces 40 hex characters
        finally:
            os.unlink(temp_path)
    
    def test_get_file_hash_sha512(self):
        """Test computing SHA512 hash."""
        from fishertools.safe.files import get_file_hash
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            result = get_file_hash(temp_path, algorithm='sha512')
            assert isinstance(result, str)
            assert len(result) == 128  # SHA512 produces 128 hex characters
        finally:
            os.unlink(temp_path)
    
    def test_get_file_hash_blake2b(self):
        """Test computing BLAKE2b hash."""
        from fishertools.safe.files import get_file_hash
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            result = get_file_hash(temp_path, algorithm='blake2b')
            assert isinstance(result, str)
            assert len(result) == 128  # BLAKE2b produces 128 hex characters
        finally:
            os.unlink(temp_path)
    
    def test_get_file_hash_nonexistent_file(self):
        """Test that FileNotFoundError is raised for non-existent file."""
        from fishertools.safe.files import get_file_hash
        
        with pytest.raises(FileNotFoundError, match="File not found"):
            get_file_hash("nonexistent_file_12345.txt")
    
    def test_get_file_hash_unsupported_algorithm(self):
        """Test that ValueError is raised for unsupported algorithm."""
        from fishertools.safe.files import get_file_hash
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError, match="Unsupported algorithm"):
                get_file_hash(temp_path, algorithm='unsupported')
        finally:
            os.unlink(temp_path)
    
    def test_get_file_hash_deterministic(self):
        """Test that hash is deterministic (same file produces same hash)."""
        from fishertools.safe.files import get_file_hash
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            hash1 = get_file_hash(temp_path)
            hash2 = get_file_hash(temp_path)
            assert hash1 == hash2
        finally:
            os.unlink(temp_path)
    
    def test_get_file_hash_accepts_string_path(self):
        """Test that get_file_hash accepts string paths."""
        from fishertools.safe.files import get_file_hash
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            result = get_file_hash(temp_path)
            assert isinstance(result, str)
        finally:
            os.unlink(temp_path)
    
    def test_get_file_hash_accepts_path_object(self):
        """Test that get_file_hash accepts Path objects."""
        from fishertools.safe.files import get_file_hash
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
            f.write("test content")
            temp_path = Path(f.name)
        
        try:
            result = get_file_hash(temp_path)
            assert isinstance(result, str)
        finally:
            os.unlink(temp_path)


class TestReadLastLines:
    """Unit tests for read_last_lines function."""
    
    def test_read_last_lines_basic(self):
        """Test reading last 10 lines from a file."""
        from fishertools.safe.files import read_last_lines
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
            for i in range(20):
                f.write(f"line {i}\n")
            temp_path = f.name
        
        try:
            result = read_last_lines(temp_path, n=10)
            assert len(result) == 10
            assert result[0] == "line 10"
            assert result[-1] == "line 19"
        finally:
            os.unlink(temp_path)
    
    def test_read_last_lines_single_line(self):
        """Test reading last 1 line."""
        from fishertools.safe.files import read_last_lines
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
            for i in range(10):
                f.write(f"line {i}\n")
            temp_path = f.name
        
        try:
            result = read_last_lines(temp_path, n=1)
            assert len(result) == 1
            assert result[0] == "line 9"
        finally:
            os.unlink(temp_path)
    
    def test_read_last_lines_n_greater_than_file_lines(self):
        """Test reading when n is greater than number of lines."""
        from fishertools.safe.files import read_last_lines
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
            for i in range(5):
                f.write(f"line {i}\n")
            temp_path = f.name
        
        try:
            result = read_last_lines(temp_path, n=10)
            assert len(result) == 5
            assert result[0] == "line 0"
            assert result[-1] == "line 4"
        finally:
            os.unlink(temp_path)
    
    def test_read_last_lines_empty_file(self):
        """Test reading from an empty file."""
        from fishertools.safe.files import read_last_lines
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
            temp_path = f.name
        
        try:
            result = read_last_lines(temp_path, n=10)
            assert result == []
        finally:
            os.unlink(temp_path)
    
    def test_read_last_lines_single_line_file(self):
        """Test reading from a file with single line."""
        from fishertools.safe.files import read_last_lines
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
            f.write("only line\n")
            temp_path = f.name
        
        try:
            result = read_last_lines(temp_path, n=10)
            assert len(result) == 1
            assert result[0] == "only line"
        finally:
            os.unlink(temp_path)
    
    def test_read_last_lines_strips_newlines(self):
        """Test that newlines are stripped from lines."""
        from fishertools.safe.files import read_last_lines
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
            f.write("line 1\nline 2\nline 3\n")
            temp_path = f.name
        
        try:
            result = read_last_lines(temp_path, n=3)
            assert all('\n' not in line for line in result)
            assert all('\r' not in line for line in result)
        finally:
            os.unlink(temp_path)
    
    def test_read_last_lines_nonexistent_file(self):
        """Test that FileNotFoundError is raised for non-existent file."""
        from fishertools.safe.files import read_last_lines
        
        with pytest.raises(FileNotFoundError, match="File not found"):
            read_last_lines("nonexistent_file_12345.txt")
    
    def test_read_last_lines_accepts_string_path(self):
        """Test that read_last_lines accepts string paths."""
        from fishertools.safe.files import read_last_lines
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
            f.write("line 1\nline 2\n")
            temp_path = f.name
        
        try:
            result = read_last_lines(temp_path, n=2)
            assert len(result) == 2
        finally:
            os.unlink(temp_path)
    
    def test_read_last_lines_accepts_path_object(self):
        """Test that read_last_lines accepts Path objects."""
        from fishertools.safe.files import read_last_lines
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
            f.write("line 1\nline 2\n")
            temp_path = Path(f.name)
        
        try:
            result = read_last_lines(temp_path, n=2)
            assert len(result) == 2
        finally:
            os.unlink(temp_path)


# ============================================================================
# Property-Based Tests using Hypothesis
# ============================================================================

class TestEnsureDirProperties:
    """Property-based tests for ensure_dir function."""
    
    @given(st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters='/\x00:<>"|?*\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f')))
    @settings(max_examples=100)
    def test_ensure_dir_returns_path_object(self, dirname):
        """Property 1: ensure_dir returns Path object
        
        **Validates: Requirements 1.1, 1.2**
        """
        from fishertools.safe.files import ensure_dir
        
        with tempfile.TemporaryDirectory() as temp_dir:
            test_path = Path(temp_dir) / dirname
            result = ensure_dir(test_path)
            assert isinstance(result, Path)
    
    @given(st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters='/\x00:<>"|?*\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f')))
    @settings(max_examples=100)
    def test_ensure_dir_creates_directory(self, dirname):
        """Property 2: ensure_dir creates directory
        
        **Validates: Requirements 1.3**
        """
        from fishertools.safe.files import ensure_dir
        
        with tempfile.TemporaryDirectory() as temp_dir:
            test_path = Path(temp_dir) / dirname
            ensure_dir(test_path)
            assert test_path.exists()
            assert test_path.is_dir()
    
    @given(st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters='/\x00:<>"|?*\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f')))
    @settings(max_examples=100)
    def test_ensure_dir_idempotent(self, dirname):
        """Property 3: ensure_dir is idempotent
        
        **Validates: Requirements 1.4**
        """
        from fishertools.safe.files import ensure_dir
        
        with tempfile.TemporaryDirectory() as temp_dir:
            test_path = Path(temp_dir) / dirname
            result1 = ensure_dir(test_path)
            result2 = ensure_dir(test_path)
            assert result1 == result2
            assert test_path.exists()


class TestGetFileHashProperties:
    """Property-based tests for get_file_hash function."""
    
    @given(
        st.binary(min_size=0, max_size=1000),
        st.sampled_from(['md5', 'sha1', 'sha256', 'sha512', 'blake2b'])
    )
    @settings(max_examples=100)
    def test_get_file_hash_supports_all_algorithms(self, content, algorithm):
        """Property 4: get_file_hash supports all algorithms
        
        **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**
        """
        from fishertools.safe.files import get_file_hash
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            result = get_file_hash(temp_path, algorithm=algorithm)
            assert isinstance(result, str)
            assert len(result) > 0
            assert all(c in '0123456789abcdef' for c in result)
        finally:
            os.unlink(temp_path)
    
    @given(st.binary(min_size=0, max_size=1000))
    @settings(max_examples=100)
    def test_get_file_hash_accepts_str_and_path(self, content):
        """Property 5: get_file_hash accepts str and Path
        
        **Validates: Requirements 2.10, 2.11**
        """
        from fishertools.safe.files import get_file_hash
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            hash_from_str = get_file_hash(temp_path)
            hash_from_path = get_file_hash(Path(temp_path))
            assert hash_from_str == hash_from_path
        finally:
            os.unlink(temp_path)
    
    @given(st.binary(min_size=0, max_size=1000))
    @settings(max_examples=100)
    def test_get_file_hash_deterministic(self, content):
        """Property 6: get_file_hash is deterministic
        
        **Validates: Requirements 2.1**
        """
        from fishertools.safe.files import get_file_hash
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            hash1 = get_file_hash(temp_path)
            hash2 = get_file_hash(temp_path)
            assert hash1 == hash2
        finally:
            os.unlink(temp_path)


class TestReadLastLinesProperties:
    """Property-based tests for read_last_lines function."""
    
    @given(
        st.lists(st.text(min_size=0, max_size=100, alphabet=st.characters(blacklist_characters='\n\r')), min_size=0, max_size=100),
        st.integers(min_value=1, max_value=50)
    )
    @settings(max_examples=100)
    def test_read_last_lines_correct_count(self, lines, n):
        """Property 7: read_last_lines returns correct number of lines
        
        **Validates: Requirements 3.1**
        """
        from fishertools.safe.files import read_last_lines
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
            for line in lines:
                f.write(line + '\n')
            temp_path = f.name
        
        try:
            result = read_last_lines(temp_path, n=n)
            expected_count = min(n, len(lines))
            assert len(result) == expected_count
        finally:
            os.unlink(temp_path)
    
    @given(
        st.lists(st.text(min_size=0, max_size=100, alphabet=st.characters(blacklist_characters='\n\r', codec='utf-8')), min_size=0, max_size=50)
    )
    @settings(max_examples=100)
    def test_read_last_lines_returns_all_when_n_greater(self, lines):
        """Property 8: read_last_lines returns all lines when n > total
        
        **Validates: Requirements 3.3**
        """
        from fishertools.safe.files import read_last_lines
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
            for line in lines:
                f.write(line + '\n')
            temp_path = f.name
        
        try:
            result = read_last_lines(temp_path, n=1000)
            assert len(result) == len(lines)
        finally:
            os.unlink(temp_path)
    
    @given(
        st.lists(st.text(min_size=0, max_size=100, alphabet=st.characters(blacklist_characters='\n\r', codec='utf-8')), min_size=0, max_size=100),
        st.integers(min_value=1, max_value=50)
    )
    @settings(max_examples=100)
    def test_read_last_lines_strips_newlines(self, lines, n):
        """Property 9: read_last_lines strips newlines
        
        **Validates: Requirements 3.11**
        """
        from fishertools.safe.files import read_last_lines
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
            for line in lines:
                f.write(line + '\n')
            temp_path = f.name
        
        try:
            result = read_last_lines(temp_path, n=n)
            assert all('\n' not in line for line in result)
            assert all('\r' not in line for line in result)
        finally:
            os.unlink(temp_path)
    
    @given(
        st.lists(st.text(min_size=0, max_size=100, alphabet=st.characters(blacklist_characters='\n\r', codec='utf-8')), min_size=0, max_size=100),
        st.integers(min_value=1, max_value=50)
    )
    @settings(max_examples=100)
    def test_read_last_lines_accepts_str_and_path(self, lines, n):
        """Property 10: read_last_lines accepts str and Path
        
        **Validates: Requirements 3.9, 3.10**
        """
        from fishertools.safe.files import read_last_lines
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
            for line in lines:
                f.write(line + '\n')
            temp_path = f.name
        
        try:
            result_from_str = read_last_lines(temp_path, n=n)
            result_from_path = read_last_lines(Path(temp_path), n=n)
            assert result_from_str == result_from_path
        finally:
            os.unlink(temp_path)


class TestModuleExports:
    """Tests for module exports."""
    
    def test_module_exports_all(self):
        """Property 11: Module exports correct functions
        
        **Validates: Requirements 4.3**
        """
        from fishertools.safe import files
        
        assert hasattr(files, '__all__')
        assert 'ensure_dir' in files.__all__
        assert 'get_file_hash' in files.__all__
        assert 'read_last_lines' in files.__all__
        assert len(files.__all__) == 3
    
    def test_module_functions_importable(self):
        """Test that all functions can be imported."""
        from fishertools.safe.files import ensure_dir, get_file_hash, read_last_lines
        
        assert callable(ensure_dir)
        assert callable(get_file_hash)
        assert callable(read_last_lines)
