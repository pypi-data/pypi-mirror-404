"""
Property-based tests for the SimpleLogger class in fishertools.patterns.

Tests the correctness properties of the SimpleLogger class using hypothesis
for property-based testing.

**Validates: Requirements 10.2, 10.3, 10.5**
"""

import pytest
import os
import tempfile
from datetime import datetime
from hypothesis import given, strategies as st, assume

from fishertools.patterns.logger import SimpleLogger


class TestSimpleLoggerWritesMessages:
    """
    Property 6: SimpleLogger Writes Messages
    
    For any message and log level, calling the appropriate logging method should
    result in the message being written to the log file with the correct level
    and a timestamp.
    
    **Validates: Requirements 10.2, 10.3**
    """
    
    def test_info_writes_message(self):
        """Test that info() writes a message to the log file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "test.log")
            logger = SimpleLogger(log_path)
            
            logger.info("Test info message")
            
            # Read the log file
            with open(log_path, 'r') as f:
                content = f.read()
            
            assert "Test info message" in content
            assert "[INFO]" in content
    
    def test_warning_writes_message(self):
        """Test that warning() writes a message to the log file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "test.log")
            logger = SimpleLogger(log_path)
            
            logger.warning("Test warning message")
            
            # Read the log file
            with open(log_path, 'r') as f:
                content = f.read()
            
            assert "Test warning message" in content
            assert "[WARNING]" in content
    
    def test_error_writes_message(self):
        """Test that error() writes a message to the log file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "test.log")
            logger = SimpleLogger(log_path)
            
            logger.error("Test error message")
            
            # Read the log file
            with open(log_path, 'r') as f:
                content = f.read()
            
            assert "Test error message" in content
            assert "[ERROR]" in content
    
    def test_message_includes_timestamp(self):
        """Test that logged messages include a timestamp."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "test.log")
            logger = SimpleLogger(log_path)
            
            logger.info("Test message")
            
            # Read the log file
            with open(log_path, 'r') as f:
                content = f.read()
            
            # Check for timestamp format YYYY-MM-DD HH:MM:SS
            import re
            timestamp_pattern = r'\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]'
            assert re.search(timestamp_pattern, content)
    
    def test_message_format_is_correct(self):
        """Test that the log message format is [TIMESTAMP] [LEVEL] message."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "test.log")
            logger = SimpleLogger(log_path)
            
            logger.info("Test message")
            
            # Read the log file
            with open(log_path, 'r') as f:
                content = f.read().strip()
            
            # Check format: [TIMESTAMP] [LEVEL] message
            import re
            pattern = r'\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] \[INFO\] Test message'
            assert re.match(pattern, content)
    
    def test_multiple_messages_are_appended(self):
        """Test that multiple messages are appended to the log file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "test.log")
            logger = SimpleLogger(log_path)
            
            logger.info("First message")
            logger.warning("Second message")
            logger.error("Third message")
            
            # Read the log file
            with open(log_path, 'r') as f:
                content = f.read()
            
            assert "First message" in content
            assert "Second message" in content
            assert "Third message" in content
            
            # Count lines
            lines = content.strip().split('\n')
            assert len(lines) == 3
    
    def test_messages_with_special_characters(self):
        """Test that messages with special characters are logged correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "test.log")
            logger = SimpleLogger(log_path)
            
            special_message = "Message with special chars: !@#$%^&*()"
            logger.info(special_message)
            
            # Read the log file
            with open(log_path, 'r') as f:
                content = f.read()
            
            assert special_message in content
    
    def test_messages_with_unicode(self):
        """Test that messages with unicode characters are logged correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "test.log")
            logger = SimpleLogger(log_path)
            
            unicode_message = "Message with unicode: 你好世界 🎉"
            logger.info(unicode_message)
            
            # Read the log file with UTF-8 encoding
            with open(log_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            assert unicode_message in content
    
    def test_messages_with_newlines(self):
        """Test that messages with newlines are logged correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "test.log")
            logger = SimpleLogger(log_path)
            
            message_with_newline = "Line 1\nLine 2"
            logger.info(message_with_newline)
            
            # Read the log file
            with open(log_path, 'r') as f:
                content = f.read()
            
            assert message_with_newline in content
    
    def test_empty_message(self):
        """Test that empty messages are logged correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "test.log")
            logger = SimpleLogger(log_path)
            
            logger.info("")
            
            # Read the log file
            with open(log_path, 'r') as f:
                content = f.read()
            
            # Should have a log entry with empty message
            assert "[INFO]" in content
    
    @given(st.text(min_size=0, max_size=500, alphabet=st.characters(blacklist_categories=('Cc', 'Cs'))))
    def test_any_message_is_logged(self, message):
        """
        Property: For any message string, calling info() should write it to
        the log file with the correct format.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "test.log")
            logger = SimpleLogger(log_path)
            
            logger.info(message)
            
            # Read the log file with UTF-8 encoding
            with open(log_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Message should be in the log
            assert message in content
            # Should have the correct level
            assert "[INFO]" in content


class TestSimpleLoggerCreatesFile:
    """
    Property 7: SimpleLogger Creates File
    
    For any log file path that doesn't exist, SimpleLogger should create the
    file when the first message is logged.
    
    **Validates: Requirements 10.5**
    """
    
    def test_creates_file_on_first_write(self):
        """Test that SimpleLogger creates the log file on first write."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "test.log")
            
            # File should not exist yet
            assert not os.path.exists(log_path)
            
            logger = SimpleLogger(log_path)
            logger.info("First message")
            
            # File should now exist
            assert os.path.exists(log_path)
            assert os.path.isfile(log_path)
    
    def test_creates_parent_directories(self):
        """Test that SimpleLogger creates parent directories if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "logs", "app", "test.log")
            
            # Parent directories should not exist
            assert not os.path.exists(os.path.dirname(log_path))
            
            logger = SimpleLogger(log_path)
            logger.info("Test message")
            
            # Parent directories should now exist
            assert os.path.exists(os.path.dirname(log_path))
            assert os.path.isfile(log_path)
    
    def test_creates_single_parent_directory(self):
        """Test that SimpleLogger creates a single parent directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "logs", "test.log")
            
            logger = SimpleLogger(log_path)
            logger.info("Test message")
            
            assert os.path.exists(log_path)
    
    def test_creates_deeply_nested_directories(self):
        """Test that SimpleLogger creates deeply nested directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "a", "b", "c", "d", "e", "test.log")
            
            logger = SimpleLogger(log_path)
            logger.info("Test message")
            
            assert os.path.exists(log_path)
    
    def test_does_not_fail_if_directory_exists(self):
        """Test that SimpleLogger doesn't fail if directory already exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = os.path.join(tmpdir, "logs")
            os.makedirs(log_dir)
            
            log_path = os.path.join(log_dir, "test.log")
            
            logger = SimpleLogger(log_path)
            logger.info("Test message")
            
            assert os.path.exists(log_path)
    
    def test_appends_to_existing_file(self):
        """Test that SimpleLogger appends to an existing log file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "test.log")
            
            # Create initial log file with content
            with open(log_path, 'w') as f:
                f.write("Initial content\n")
            
            logger = SimpleLogger(log_path)
            logger.info("New message")
            
            # Read the log file
            with open(log_path, 'r') as f:
                content = f.read()
            
            # Both messages should be present
            assert "Initial content" in content
            assert "New message" in content
    
    def test_file_path_attribute_is_set(self):
        """Test that file_path attribute is set correctly."""
        log_path = "test/path/app.log"
        logger = SimpleLogger(log_path)
        
        assert logger.file_path == log_path
    
    @given(st.lists(st.text(
        alphabet="abcdefghijklmnopqrstuvwxyz0123456789_-",
        min_size=1,
        max_size=20
    ), min_size=1, max_size=5))
    def test_creates_file_for_any_path(self, path_parts):
        """
        Property: For any valid path with non-existent parent directories,
        SimpleLogger should create the file when logging.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Build a nested path
            nested_path = os.path.join(tmpdir, *path_parts)
            log_path = os.path.join(nested_path, "test.log")
            
            logger = SimpleLogger(log_path)
            logger.info("Test message")
            
            # File should exist
            assert os.path.exists(log_path)
            assert os.path.isfile(log_path)


class TestSimpleLoggerIntegration:
    """Integration tests for SimpleLogger."""
    
    def test_multiple_loggers_same_file(self):
        """Test that multiple logger instances can write to the same file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "shared.log")
            
            logger1 = SimpleLogger(log_path)
            logger1.info("Message from logger 1")
            
            logger2 = SimpleLogger(log_path)
            logger2.warning("Message from logger 2")
            
            # Read the log file
            with open(log_path, 'r') as f:
                content = f.read()
            
            assert "Message from logger 1" in content
            assert "Message from logger 2" in content
    
    def test_all_log_levels(self):
        """Test that all log levels work correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "test.log")
            logger = SimpleLogger(log_path)
            
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            
            # Read the log file
            with open(log_path, 'r') as f:
                content = f.read()
            
            assert "[INFO]" in content
            assert "[WARNING]" in content
            assert "[ERROR]" in content
            assert "Info message" in content
            assert "Warning message" in content
            assert "Error message" in content
    
    def test_logger_with_relative_path(self):
        """Test that SimpleLogger works with relative paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                
                logger = SimpleLogger("test.log")
                logger.info("Test message")
                
                assert os.path.exists("test.log")
                
                with open("test.log", 'r') as f:
                    content = f.read()
                
                assert "Test message" in content
            finally:
                os.chdir(original_cwd)
    
    def test_logger_with_absolute_path(self):
        """Test that SimpleLogger works with absolute paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.abspath(os.path.join(tmpdir, "test.log"))
            logger = SimpleLogger(log_path)
            
            logger.info("Test message")
            
            assert os.path.exists(log_path)
    
    def test_logger_preserves_message_content(self):
        """Test that SimpleLogger preserves exact message content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "test.log")
            logger = SimpleLogger(log_path)
            
            messages = [
                "Simple message",
                "Message with numbers 12345",
                "Message with symbols !@#$%",
                "Message with quotes 'single' and \"double\"",
                "Message with tabs\tand\tspaces"
            ]
            
            for msg in messages:
                logger.info(msg)
            
            # Read the log file
            with open(log_path, 'r') as f:
                content = f.read()
            
            # All messages should be preserved
            for msg in messages:
                assert msg in content


class TestSimpleLoggerErrorHandling:
    """Test error handling in SimpleLogger."""
    
    def test_raises_ioerror_for_invalid_path(self):
        """Test that SimpleLogger raises an error for invalid paths."""
        # Use a path that will fail during file operations
        # On Windows, we can use a reserved device name
        invalid_path = "CON"  # Reserved device name on Windows
        logger = SimpleLogger(invalid_path)
        
        with pytest.raises((IOError, OSError, ValueError)):
            logger.info("Test message")
    
    def test_raises_ioerror_for_permission_denied(self):
        """Test that SimpleLogger raises IOError for permission denied."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "test.log")
            logger = SimpleLogger(log_path)
            
            # Create the file
            logger.info("Initial message")
            
            # Make the file read-only
            os.chmod(log_path, 0o444)
            
            try:
                # Try to write to read-only file
                with pytest.raises(IOError):
                    logger.info("Another message")
            finally:
                # Restore permissions for cleanup
                os.chmod(log_path, 0o644)

