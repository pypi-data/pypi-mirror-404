"""
Unit tests for the CommandParser class.
"""

import pytest
from fishertools.learn.repl.command_parser import CommandParser


class TestCommandParserBasic:
    """Test basic command parsing functionality."""
    
    def test_parse_simple_command(self):
        """Test parsing a simple command without arguments."""
        cmd_type, args = CommandParser.parse("/help")
        assert cmd_type == "command"
        assert args == ["help"]
    
    def test_parse_command_with_arguments(self):
        """Test parsing a command with arguments."""
        cmd_type, args = CommandParser.parse("/search python")
        assert cmd_type == "command"
        assert args == ["search", "python"]
    
    def test_parse_command_with_multiple_arguments(self):
        """Test parsing a command with multiple arguments."""
        cmd_type, args = CommandParser.parse("/search python lists")
        assert cmd_type == "command"
        assert args == ["search", "python", "lists"]
    
    def test_parse_topic_name(self):
        """Test parsing a topic name (no leading /)."""
        cmd_type, args = CommandParser.parse("Lists")
        assert cmd_type == "topic"
        assert args == ["Lists"]
    
    def test_parse_topic_with_spaces(self):
        """Test parsing a topic name with spaces."""
        cmd_type, args = CommandParser.parse("For Loops")
        assert cmd_type == "topic"
        assert args == ["For Loops"]
    
    def test_parse_quoted_arguments(self):
        """Test parsing command with quoted arguments."""
        cmd_type, args = CommandParser.parse('/search "list comprehension"')
        assert cmd_type == "command"
        assert args == ["search", "list comprehension"]
    
    def test_parse_empty_input_raises_error(self):
        """Test that empty input raises ValueError."""
        with pytest.raises(ValueError):
            CommandParser.parse("")
    
    def test_parse_whitespace_only_raises_error(self):
        """Test that whitespace-only input raises ValueError."""
        with pytest.raises(ValueError):
            CommandParser.parse("   ")
    
    def test_parse_invalid_command_raises_error(self):
        """Test that invalid command raises ValueError."""
        with pytest.raises(ValueError):
            CommandParser.parse("/invalid_command")
    
    def test_parse_command_only_slash_raises_error(self):
        """Test that just "/" raises ValueError."""
        with pytest.raises(ValueError):
            CommandParser.parse("/")
    
    def test_parse_command_case_insensitive(self):
        """Test that commands are case-insensitive."""
        cmd_type1, args1 = CommandParser.parse("/HELP")
        cmd_type2, args2 = CommandParser.parse("/Help")
        cmd_type3, args3 = CommandParser.parse("/help")
        
        assert args1 == args2 == args3 == ["help"]
    
    def test_parse_topic_case_preserved(self):
        """Test that topic names preserve case."""
        cmd_type, args = CommandParser.parse("Lists")
        assert args == ["Lists"]
        
        cmd_type, args = CommandParser.parse("lists")
        assert args == ["lists"]


class TestCommandParserEdgeCases:
    """Test edge cases in command parsing."""
    
    def test_parse_command_with_leading_trailing_spaces(self):
        """Test parsing command with leading/trailing spaces."""
        cmd_type, args = CommandParser.parse("  /help  ")
        assert cmd_type == "command"
        assert args == ["help"]
    
    def test_parse_topic_with_leading_trailing_spaces(self):
        """Test parsing topic with leading/trailing spaces."""
        cmd_type, args = CommandParser.parse("  Lists  ")
        assert cmd_type == "topic"
        assert args == ["Lists"]
    
    def test_parse_command_with_extra_spaces_between_args(self):
        """Test parsing command with extra spaces between arguments."""
        cmd_type, args = CommandParser.parse("/search   python   lists")
        assert cmd_type == "command"
        assert args == ["search", "python", "lists"]
    
    def test_parse_command_with_special_characters_in_args(self):
        """Test parsing command with special characters in arguments."""
        cmd_type, args = CommandParser.parse("/search list[0]")
        assert cmd_type == "command"
        assert args == ["search", "list[0]"]


class TestCommandParserUtilityMethods:
    """Test utility methods of CommandParser."""
    
    def test_is_command_true(self):
        """Test is_command returns True for commands."""
        assert CommandParser.is_command("/help") is True
        assert CommandParser.is_command("/search python") is True
    
    def test_is_command_false(self):
        """Test is_command returns False for non-commands."""
        assert CommandParser.is_command("Lists") is False
        assert CommandParser.is_command("python") is False
    
    def test_extract_command_name(self):
        """Test extracting command name from command string."""
        assert CommandParser.extract_command_name("/help") == "help"
        assert CommandParser.extract_command_name("/SEARCH") == "search"
        assert CommandParser.extract_command_name("/search python") == "search"
    
    def test_extract_command_name_invalid_input(self):
        """Test extract_command_name with invalid input."""
        with pytest.raises(ValueError):
            CommandParser.extract_command_name("Lists")
    
    def test_normalize_topic_name(self):
        """Test normalizing topic names."""
        assert CommandParser.normalize_topic_name("Lists") == "Lists"
        assert CommandParser.normalize_topic_name("  Lists  ") == "Lists"
        assert CommandParser.normalize_topic_name("For Loops") == "For Loops"


class TestCommandParserAllValidCommands:
    """Test that all valid commands can be parsed."""
    
    def test_all_valid_commands(self):
        """Test parsing all valid commands."""
        valid_commands = [
            "help", "list", "search", "random", "categories", "category",
            "path", "related", "progress", "stats", "hint", "tip", "tips",
            "run", "modify", "exit_edit", "history", "clear_history", "session",
            "reset_progress", "commands", "about", "tutorial", "next", "prev",
            "goto", "exit", "quit"
        ]
        
        for cmd in valid_commands:
            cmd_type, args = CommandParser.parse(f"/{cmd}")
            assert cmd_type == "command"
            assert args[0] == cmd
