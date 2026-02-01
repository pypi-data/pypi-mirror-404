"""
Command parser for the Knowledge Engine REPL.

This module handles parsing user input to identify commands, topic names, and edit mode input.
"""

import shlex
from typing import Tuple, List


class CommandParser:
    """
    Parses user input to identify command type and extract arguments.
    
    Supports three input types:
    - Commands: Start with "/" (e.g., "/help", "/search python")
    - Topic names: Regular text matching a topic in the Knowledge Engine
    - Edit mode input: Code or commands while in edit mode
    """
    
    # Error message constants
    EMPTY_COMMAND_ERROR = "Command cannot be empty"
    
    # Commands that are recognized by the REPL
    VALID_COMMANDS = {
        "help", "list", "search", "random", "categories", "category",
        "path", "related", "progress", "stats", "hint", "tip", "tips",
        "run", "modify", "exit_edit", "history", "clear_history", "session",
        "reset_progress", "commands", "about", "tutorial", "next", "prev",
        "goto", "exit", "quit"
    }
    
    @staticmethod
    def parse(input_str: str) -> Tuple[str, List[str]]:
        """
        Parse user input into command type and arguments.
        
        Args:
            input_str: The user input string
        
        Returns:
            Tuple of (command_type, arguments) where:
            - command_type: 'command', 'topic', or 'edit'
            - arguments: List of argument strings
        
        Raises:
            ValueError: If input cannot be parsed
        
        Example:
            >>> parser = CommandParser()
            >>> cmd_type, args = parser.parse("/help")
            >>> cmd_type
            'command'
            >>> args
            ['help']
            
            >>> cmd_type, args = parser.parse("/search python")
            >>> args
            ['search', 'python']
            
            >>> cmd_type, args = parser.parse("Lists")
            >>> cmd_type
            'topic'
            >>> args
            ['Lists']
        """
        if not input_str or not input_str.strip():
            raise ValueError("Input cannot be empty")
        
        input_str = input_str.strip()
        
        # Check if it's a command (starts with /)
        if input_str.startswith("/"):
            return CommandParser._parse_command(input_str)
        
        # Otherwise it's a topic name or edit mode input
        return "topic", [input_str]
    
    @staticmethod
    def _parse_command(input_str: str) -> Tuple[str, List[str]]:
        """
        Parse a command string (starts with /).
        
        Args:
            input_str: Command string starting with /
        
        Returns:
            Tuple of ('command', [command_name, arg1, arg2, ...])
        
        Raises:
            ValueError: If command format is invalid
        """
        # Remove leading /
        command_str = input_str[1:].strip()
        
        if not command_str:
            raise ValueError(CommandParser.EMPTY_COMMAND_ERROR)
        
        # Use shlex to handle quoted arguments
        try:
            parts = shlex.split(command_str)
        except ValueError as e:
            raise ValueError(f"Invalid command format: {e}")
        
        if not parts:
            raise ValueError(CommandParser.EMPTY_COMMAND_ERROR)
        
        command_name = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        # Validate command name
        if command_name not in CommandParser.VALID_COMMANDS:
            raise ValueError(f"Unknown command: {command_name}")
        
        return "command", [command_name] + args
    
    @staticmethod
    def normalize_topic_name(name: str) -> str:
        """
        Normalize a topic name for comparison.
        
        Args:
            name: The topic name to normalize
        
        Returns:
            Normalized topic name (preserves case but strips whitespace)
        """
        return name.strip()
    
    @staticmethod
    def is_command(input_str: str) -> bool:
        """
        Check if input is a command.
        
        Args:
            input_str: The input string to check
        
        Returns:
            True if input starts with /
        """
        return input_str.strip().startswith("/")
    
    @staticmethod
    def extract_command_name(input_str: str) -> str:
        """
        Extract just the command name from a command string.
        
        Args:
            input_str: Command string starting with /
        
        Returns:
            The command name (lowercase)
        
        Raises:
            ValueError: If input is not a valid command
        """
        if not input_str.startswith("/"):
            raise ValueError("Not a command")
        
        command_str = input_str[1:].strip()
        if not command_str:
            raise ValueError(CommandParser.EMPTY_COMMAND_ERROR)
        
        try:
            parts = shlex.split(command_str)
            return parts[0].lower()
        except ValueError as e:
            raise ValueError(f"Invalid command format: {e}")
