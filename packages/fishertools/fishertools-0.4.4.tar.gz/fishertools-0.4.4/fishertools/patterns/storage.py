"""
JSONStorage pattern for persistent data storage.

This module provides the JSONStorage class for saving and loading data
in JSON format without requiring manual file handling code.

Example:
    storage = JSONStorage("data.json")
    storage.save({"name": "Alice", "age": 30})
    data = storage.load()
    print(data)  # {"name": "Alice", "age": 30}
"""

import json
import os
from pathlib import Path


class JSONStorage:
    """
    Persist and retrieve data in JSON format.

    This class handles all file operations for JSON data storage, including
    automatic directory creation and error handling. Data is stored in a
    human-readable JSON format.

    Parameters:
        file_path (str): Path to the JSON file for storage. Parent directories
                        are created automatically if they don't exist.

    Attributes:
        file_path (str): The path to the JSON storage file.

    Methods:
        save(data): Write data to the JSON file.
        load(): Read data from the JSON file.
        exists(): Check if the storage file exists.

    Raises:
        IOError: If file operations fail.
        json.JSONDecodeError: If the JSON file is corrupted.

    Example:
        storage = JSONStorage("config/app.json")
        storage.save({"theme": "dark", "language": "en"})
        config = storage.load()
        if storage.exists():
            print("Config file exists")

    Note:
        - Parent directories are created automatically
        - File is created on first save if it doesn't exist
        - Existing files are overwritten when saving
        - Load returns an empty dict if file doesn't exist
    """

    def __init__(self, file_path):
        """
        Initialize JSONStorage with a file path.

        Parameters:
            file_path (str): Path to the JSON storage file.
        """
        self.file_path = file_path

    def save(self, data):
        """
        Save data to the JSON file.

        Parameters:
            data (dict): Data to save. Must be JSON-serializable.

        Returns:
            None

        Raises:
            IOError: If file write fails.
            TypeError: If data is not JSON-serializable.
        """
        try:
            # Create parent directories if they don't exist
            parent_dir = os.path.dirname(self.file_path)
            if parent_dir:
                Path(parent_dir).mkdir(parents=True, exist_ok=True)
            
            # Write data to JSON file
            with open(self.file_path, 'w') as f:
                json.dump(data, f, indent=2)
        except TypeError as e:
            raise TypeError(f"Data is not JSON-serializable: {e}")
        except IOError as e:
            raise IOError(f"Failed to write to {self.file_path}: {e}")

    def load(self):
        """
        Load data from the JSON file.

        Returns:
            dict: The loaded data, or empty dict if file doesn't exist.

        Raises:
            IOError: If file read fails.
            json.JSONDecodeError: If the JSON file is corrupted.
        """
        try:
            if not os.path.exists(self.file_path):
                return {}
            
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Failed to parse JSON from {self.file_path}: {e.msg}",
                e.doc,
                e.pos
            )
        except IOError as e:
            raise IOError(f"Failed to read from {self.file_path}: {e}")

    def exists(self):
        """
        Check if the storage file exists.

        Returns:
            bool: True if the file exists, False otherwise.
        """
        return os.path.exists(self.file_path)
