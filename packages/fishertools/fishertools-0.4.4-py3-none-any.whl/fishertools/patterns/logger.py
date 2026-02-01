"""
SimpleLogger pattern for file-based logging.

This module provides the SimpleLogger class for adding logging to applications
without complex configuration. Messages are written to a file with timestamps
and log levels.

Example:
    logger = SimpleLogger("app.log")
    logger.info("Application started")
    logger.warning("Low memory detected")
    logger.error("Connection failed")
"""

import os
from datetime import datetime
from pathlib import Path


class SimpleLogger:
    """
    Simple file-based logging with timestamps and levels.

    This class provides a straightforward way to log messages to a file with
    automatic timestamps and log level indicators. No configuration is required.

    Parameters:
        file_path (str): Path to the log file. Created automatically if it
                        doesn't exist. Parent directories are created as needed.

    Attributes:
        file_path (str): The path to the log file.

    Methods:
        info(message): Log an info-level message.
        warning(message): Log a warning-level message.
        error(message): Log an error-level message.

    Raises:
        IOError: If file operations fail.

    Example:
        logger = SimpleLogger("logs/app.log")
        logger.info("User logged in")
        logger.warning("Deprecated function used")
        logger.error("Database connection failed")

    Note:
        - Log format: [TIMESTAMP] [LEVEL] message
        - Timestamp format: YYYY-MM-DD HH:MM:SS
        - Messages are appended to the file
        - File is created automatically on first write
        - Parent directories are created automatically
    """

    def __init__(self, file_path):
        """
        Initialize SimpleLogger with a file path.

        Parameters:
            file_path (str): Path to the log file.
        """
        self.file_path = file_path

    def info(self, message):
        """
        Log an info-level message.

        Parameters:
            message (str): The message to log.

        Returns:
            None

        Raises:
            IOError: If file write fails.
        """
        self._log("INFO", message)

    def warning(self, message):
        """
        Log a warning-level message.

        Parameters:
            message (str): The message to log.

        Returns:
            None

        Raises:
            IOError: If file write fails.
        """
        self._log("WARNING", message)

    def error(self, message):
        """
        Log an error-level message.

        Parameters:
            message (str): The message to log.

        Returns:
            None

        Raises:
            IOError: If file write fails.
        """
        self._log("ERROR", message)

    def _log(self, level, message):
        """
        Internal method to write a log message.

        Parameters:
            level (str): The log level (INFO, WARNING, ERROR).
            message (str): The message to log.

        Returns:
            None

        Raises:
            IOError: If file write fails.
        """
        try:
            # Create parent directories if they don't exist
            parent_dir = os.path.dirname(self.file_path)
            if parent_dir:
                Path(parent_dir).mkdir(parents=True, exist_ok=True)
            
            # Get current timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Format log message
            log_entry = f"[{timestamp}] [{level}] {message}\n"
            
            # Append to log file with UTF-8 encoding
            with open(self.file_path, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except IOError as e:
            raise IOError(f"Failed to write to {self.file_path}: {e}")
