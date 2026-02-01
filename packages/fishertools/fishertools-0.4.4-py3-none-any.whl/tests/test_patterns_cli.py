"""
Property-based tests for the SimpleCLI class in fishertools.patterns.

Tests the correctness properties of the SimpleCLI class using hypothesis
for property-based testing.

**Validates: Requirements 11.2, 11.3, 11.5**
"""

import pytest
from unittest.mock import patch, MagicMock
from io import StringIO

from fishertools.patterns.cli import SimpleCLI


class TestSimpleCLIExecutesCorrectHandler:
    """
    Property 8: SimpleCLI Executes Correct Handler
    
    For any registered command, calling SimpleCLI with that command should
    execute the corresponding handler function.
    
    **Validates: Requirements 11.2, 11.3**
    """
    
    def test_executes_single_command(self):
        """Test that SimpleCLI executes a single registered command."""
        cli = SimpleCLI("test", "Test CLI")
        mock_handler = MagicMock()
        
        @cli.command("test", "Test command")
        def test_cmd():
            mock_handler()
        
        cli.run(["test"])
        
        mock_handler.assert_called_once()
    
    def test_executes_correct_command_from_multiple(self):
        """Test that SimpleCLI executes the correct command from multiple options."""
        cli = SimpleCLI("test", "Test CLI")
        mock_handler1 = MagicMock()
        mock_handler2 = MagicMock()
        mock_handler3 = MagicMock()
        
        @cli.command("cmd1", "First command")
        def cmd1():
            mock_handler1()
        
        @cli.command("cmd2", "Second command")
        def cmd2():
            mock_handler2()
        
        @cli.command("cmd3", "Third command")
        def cmd3():
            mock_handler3()
        
        # Execute cmd2
        cli.run(["cmd2"])
        
        # Only cmd2 should have been called
        mock_handler1.assert_not_called()
        mock_handler2.assert_called_once()
        mock_handler3.assert_not_called()
    
    def test_executes_command_with_arguments(self):
        """Test that SimpleCLI passes arguments to the command handler."""
        cli = SimpleCLI("test", "Test CLI")
        mock_handler = MagicMock()
        
        @cli.command("greet", "Greet someone")
        def greet(name):
            mock_handler(name)
        
        cli.run(["greet", "Alice"])
        
        mock_handler.assert_called_once_with("Alice")
    
    def test_executes_command_with_multiple_arguments(self):
        """Test that SimpleCLI passes multiple arguments to the command handler."""
        cli = SimpleCLI("test", "Test CLI")
        mock_handler = MagicMock()
        
        @cli.command("add", "Add two numbers")
        def add(a, b):
            mock_handler(a, b)
        
        cli.run(["add", "5", "3"])
        
        mock_handler.assert_called_once_with("5", "3")
    
    def test_executes_command_with_many_arguments(self):
        """Test that SimpleCLI passes many arguments to the command handler."""
        cli = SimpleCLI("test", "Test CLI")
        mock_handler = MagicMock()
        
        @cli.command("multi", "Multi-argument command")
        def multi(a, b, c, d, e):
            mock_handler(a, b, c, d, e)
        
        cli.run(["multi", "1", "2", "3", "4", "5"])
        
        mock_handler.assert_called_once_with("1", "2", "3", "4", "5")
    
    def test_executes_command_with_no_arguments(self):
        """Test that SimpleCLI executes command with no arguments."""
        cli = SimpleCLI("test", "Test CLI")
        mock_handler = MagicMock()
        
        @cli.command("status", "Show status")
        def status():
            mock_handler()
        
        cli.run(["status"])
        
        mock_handler.assert_called_once()
    
    def test_command_receives_arguments_as_strings(self):
        """Test that command arguments are passed as strings."""
        cli = SimpleCLI("test", "Test CLI")
        received_args = []
        
        @cli.command("echo", "Echo arguments")
        def echo(*args):
            received_args.extend(args)
        
        cli.run(["echo", "hello", "123", "true"])
        
        # All arguments should be strings
        assert received_args == ["hello", "123", "true"]
        assert all(isinstance(arg, str) for arg in received_args)
    
    def test_executes_command_with_special_characters_in_args(self):
        """Test that SimpleCLI handles special characters in arguments."""
        cli = SimpleCLI("test", "Test CLI")
        mock_handler = MagicMock()
        
        @cli.command("special", "Handle special chars")
        def special(arg):
            mock_handler(arg)
        
        cli.run(["special", "!@#$%^&*()"])
        
        mock_handler.assert_called_once_with("!@#$%^&*()")
    
    def test_executes_command_with_empty_string_argument(self):
        """Test that SimpleCLI handles empty string arguments."""
        cli = SimpleCLI("test", "Test CLI")
        mock_handler = MagicMock()
        
        @cli.command("empty", "Handle empty string")
        def empty(arg):
            mock_handler(arg)
        
        cli.run(["empty", ""])
        
        mock_handler.assert_called_once_with("")
    
    def test_executes_command_with_space_in_argument(self):
        """Test that SimpleCLI handles arguments with spaces."""
        cli = SimpleCLI("test", "Test CLI")
        mock_handler = MagicMock()
        
        @cli.command("msg", "Send message")
        def msg(text):
            mock_handler(text)
        
        cli.run(["msg", "hello world"])
        
        mock_handler.assert_called_once_with("hello world")
    
    def test_command_decorator_returns_function(self):
        """Test that command decorator returns the original function."""
        cli = SimpleCLI("test", "Test CLI")
        
        @cli.command("test", "Test command")
        def test_func():
            return "result"
        
        # The decorator should return the original function
        assert test_func() == "result"
    
    def test_multiple_commands_registered_independently(self):
        """Test that multiple commands are registered independently."""
        cli = SimpleCLI("test", "Test CLI")
        results = []
        
        @cli.command("cmd1", "First")
        def cmd1():
            results.append("cmd1")
        
        @cli.command("cmd2", "Second")
        def cmd2():
            results.append("cmd2")
        
        cli.run(["cmd1"])
        cli.run(["cmd2"])
        cli.run(["cmd1"])
        
        assert results == ["cmd1", "cmd2", "cmd1"]
    
    def test_command_with_return_value(self):
        """Test that command handlers can return values."""
        cli = SimpleCLI("test", "Test CLI")
        
        @cli.command("get", "Get value")
        def get_value():
            return 42
        
        # The handler should execute without error
        cli.run(["get"])


class TestSimpleCLIHandlesInvalidCommands:
    """
    Property 9: SimpleCLI Handles Invalid Commands
    
    For any invalid command, SimpleCLI should handle it gracefully without
    crashing.
    
    **Validates: Requirements 11.5**
    """
    
    def test_handles_unknown_command(self):
        """Test that SimpleCLI handles unknown commands gracefully."""
        cli = SimpleCLI("test", "Test CLI")
        
        @cli.command("known", "Known command")
        def known():
            pass
        
        # Should not raise an exception
        with patch('builtins.print') as mock_print:
            cli.run(["unknown"])
        
        # Should print an error message
        printed_text = ' '.join(str(call) for call in mock_print.call_args_list)
        assert "Error" in printed_text or "error" in printed_text.lower()
    
    def test_handles_invalid_command_gracefully(self):
        """Test that SimpleCLI doesn't crash on invalid commands."""
        cli = SimpleCLI("test", "Test CLI")
        
        @cli.command("valid", "Valid command")
        def valid():
            pass
        
        # Should not raise an exception
        try:
            cli.run(["invalid"])
        except Exception as e:
            pytest.fail(f"SimpleCLI raised an exception: {e}")
    
    def test_shows_help_on_invalid_command(self):
        """Test that SimpleCLI shows help when command is invalid."""
        cli = SimpleCLI("test", "Test CLI")
        
        @cli.command("valid", "Valid command")
        def valid():
            pass
        
        with patch('builtins.print') as mock_print:
            cli.run(["invalid"])
        
        # Should print help information
        printed_text = ' '.join(str(call) for call in mock_print.call_args_list)
        assert "Available commands" in printed_text or "valid" in printed_text.lower()
    
    def test_handles_wrong_number_of_arguments(self):
        """Test that SimpleCLI handles wrong number of arguments gracefully."""
        cli = SimpleCLI("test", "Test CLI")
        
        @cli.command("add", "Add two numbers")
        def add(a, b):
            pass
        
        # Should not raise an exception
        with patch('builtins.print') as mock_print:
            cli.run(["add", "5"])  # Missing second argument
        
        # Should print an error message
        printed_text = ' '.join(str(call) for call in mock_print.call_args_list)
        assert "Error" in printed_text or "error" in printed_text.lower()
    
    def test_handles_too_many_arguments(self):
        """Test that SimpleCLI handles too many arguments gracefully."""
        cli = SimpleCLI("test", "Test CLI")
        
        @cli.command("single", "Single argument command")
        def single(arg):
            pass
        
        # Should not raise an exception
        with patch('builtins.print') as mock_print:
            cli.run(["single", "arg1", "arg2", "arg3"])
        
        # Should print an error message
        printed_text = ' '.join(str(call) for call in mock_print.call_args_list)
        assert "Error" in printed_text or "error" in printed_text.lower()
    
    def test_handles_empty_command_list(self):
        """Test that SimpleCLI handles empty command list gracefully."""
        cli = SimpleCLI("test", "Test CLI")
        
        @cli.command("cmd", "Command")
        def cmd():
            pass
        
        # Should not raise an exception
        with patch('builtins.print') as mock_print:
            cli.run([])
        
        # Should show help
        printed_text = ' '.join(str(call) for call in mock_print.call_args_list)
        assert "Available commands" in printed_text or "test" in printed_text.lower()
    
    def test_handles_help_flag(self):
        """Test that SimpleCLI handles --help flag gracefully."""
        cli = SimpleCLI("test", "Test CLI")
        
        @cli.command("cmd", "Command")
        def cmd():
            pass
        
        # Should not raise an exception
        with patch('builtins.print') as mock_print:
            cli.run(["--help"])
        
        # Should show help
        printed_text = ' '.join(str(call) for call in mock_print.call_args_list)
        assert "Available commands" in printed_text
    
    def test_handles_short_help_flag(self):
        """Test that SimpleCLI handles -h flag gracefully."""
        cli = SimpleCLI("test", "Test CLI")
        
        @cli.command("cmd", "Command")
        def cmd():
            pass
        
        # Should not raise an exception
        with patch('builtins.print') as mock_print:
            cli.run(["-h"])
        
        # Should show help
        printed_text = ' '.join(str(call) for call in mock_print.call_args_list)
        assert "Available commands" in printed_text
    
    def test_handles_command_that_raises_exception(self):
        """Test that SimpleCLI handles exceptions in command handlers."""
        cli = SimpleCLI("test", "Test CLI")
        
        @cli.command("fail", "Failing command")
        def fail():
            raise ValueError("Command failed")
        
        # Should not raise an exception to the caller
        try:
            cli.run(["fail"])
        except ValueError:
            pytest.fail("SimpleCLI should handle exceptions in handlers")
    
    def test_handles_no_commands_registered(self):
        """Test that SimpleCLI handles case with no commands registered."""
        cli = SimpleCLI("test", "Test CLI")
        
        # Should not raise an exception
        with patch('builtins.print') as mock_print:
            cli.run(["anything"])
        
        # Should show error and help
        printed_text = ' '.join(str(call) for call in mock_print.call_args_list)
        assert "Error" in printed_text or "error" in printed_text.lower()
    
    def test_handles_case_sensitive_commands(self):
        """Test that SimpleCLI treats commands as case-sensitive."""
        cli = SimpleCLI("test", "Test CLI")
        mock_handler = MagicMock()
        
        @cli.command("Test", "Test command")
        def test_cmd():
            mock_handler()
        
        # Try with different case
        with patch('builtins.print') as mock_print:
            cli.run(["test"])
        
        # Should not find the command (case-sensitive)
        mock_handler.assert_not_called()
        printed_text = ' '.join(str(call) for call in mock_print.call_args_list)
        assert "Error" in printed_text or "error" in printed_text.lower()
    
    def test_handles_command_with_special_characters(self):
        """Test that SimpleCLI handles commands with special characters."""
        cli = SimpleCLI("test", "Test CLI")
        mock_handler = MagicMock()
        
        @cli.command("test-cmd", "Test command")
        def test_cmd():
            mock_handler()
        
        cli.run(["test-cmd"])
        
        mock_handler.assert_called_once()
    
    def test_handles_command_with_underscores(self):
        """Test that SimpleCLI handles commands with underscores."""
        cli = SimpleCLI("test", "Test CLI")
        mock_handler = MagicMock()
        
        @cli.command("test_cmd", "Test command")
        def test_cmd():
            mock_handler()
        
        cli.run(["test_cmd"])
        
        mock_handler.assert_called_once()


class TestSimpleCLIHelpDisplay:
    """Test help display functionality."""
    
    def test_shows_application_name(self):
        """Test that help displays the application name."""
        cli = SimpleCLI("MyApp", "My application")
        
        with patch('builtins.print') as mock_print:
            cli.run(["--help"])
        
        printed_text = ' '.join(str(call) for call in mock_print.call_args_list)
        assert "MyApp" in printed_text
    
    def test_shows_application_description(self):
        """Test that help displays the application description."""
        cli = SimpleCLI("MyApp", "This is my application")
        
        with patch('builtins.print') as mock_print:
            cli.run(["--help"])
        
        printed_text = ' '.join(str(call) for call in mock_print.call_args_list)
        assert "This is my application" in printed_text
    
    def test_shows_all_commands(self):
        """Test that help displays all registered commands."""
        cli = SimpleCLI("test", "Test CLI")
        
        @cli.command("cmd1", "First command")
        def cmd1():
            pass
        
        @cli.command("cmd2", "Second command")
        def cmd2():
            pass
        
        @cli.command("cmd3", "Third command")
        def cmd3():
            pass
        
        with patch('builtins.print') as mock_print:
            cli.run(["--help"])
        
        printed_text = ' '.join(str(call) for call in mock_print.call_args_list)
        assert "cmd1" in printed_text
        assert "cmd2" in printed_text
        assert "cmd3" in printed_text
    
    def test_shows_command_descriptions(self):
        """Test that help displays command descriptions."""
        cli = SimpleCLI("test", "Test CLI")
        
        @cli.command("greet", "Greet someone")
        def greet():
            pass
        
        @cli.command("goodbye", "Say goodbye")
        def goodbye():
            pass
        
        with patch('builtins.print') as mock_print:
            cli.run(["--help"])
        
        printed_text = ' '.join(str(call) for call in mock_print.call_args_list)
        assert "Greet someone" in printed_text
        assert "Say goodbye" in printed_text
    
    def test_shows_available_commands_header(self):
        """Test that help shows 'Available commands' header."""
        cli = SimpleCLI("test", "Test CLI")
        
        @cli.command("cmd", "Command")
        def cmd():
            pass
        
        with patch('builtins.print') as mock_print:
            cli.run(["--help"])
        
        printed_text = ' '.join(str(call) for call in mock_print.call_args_list)
        assert "Available commands" in printed_text


class TestSimpleCLIInitialization:
    """Test SimpleCLI initialization."""
    
    def test_stores_name(self):
        """Test that SimpleCLI stores the application name."""
        cli = SimpleCLI("MyApp", "Description")
        assert cli.name == "MyApp"
    
    def test_stores_description(self):
        """Test that SimpleCLI stores the application description."""
        cli = SimpleCLI("MyApp", "My description")
        assert cli.description == "My description"
    
    def test_initializes_empty_commands(self):
        """Test that SimpleCLI initializes with empty commands."""
        cli = SimpleCLI("MyApp", "Description")
        assert cli.commands == {}
    
    def test_has_docstring(self):
        """Test that SimpleCLI has a docstring."""
        assert SimpleCLI.__doc__ is not None
        assert len(SimpleCLI.__doc__) > 0
    
    def test_command_method_has_docstring(self):
        """Test that command method has a docstring."""
        cli = SimpleCLI("test", "test")
        assert cli.command.__doc__ is not None
        assert len(cli.command.__doc__) > 0
    
    def test_run_method_has_docstring(self):
        """Test that run method has a docstring."""
        cli = SimpleCLI("test", "test")
        assert cli.run.__doc__ is not None
        assert len(cli.run.__doc__) > 0


class TestSimpleCLIIntegration:
    """Integration tests for SimpleCLI."""
    
    def test_full_workflow(self):
        """Test a complete workflow with SimpleCLI."""
        cli = SimpleCLI("calculator", "Simple calculator")
        results = []
        
        @cli.command("add", "Add two numbers")
        def add(a, b):
            results.append(int(a) + int(b))
        
        @cli.command("multiply", "Multiply two numbers")
        def multiply(a, b):
            results.append(int(a) * int(b))
        
        cli.run(["add", "5", "3"])
        cli.run(["multiply", "4", "2"])
        
        assert results == [8, 8]
    
    def test_multiple_cli_instances(self):
        """Test that multiple SimpleCLI instances work independently."""
        cli1 = SimpleCLI("app1", "App 1")
        cli2 = SimpleCLI("app2", "App 2")
        
        results = []
        
        @cli1.command("cmd", "Command")
        def cmd1():
            results.append("cli1")
        
        @cli2.command("cmd", "Command")
        def cmd2():
            results.append("cli2")
        
        cli1.run(["cmd"])
        cli2.run(["cmd"])
        
        assert results == ["cli1", "cli2"]
    
    def test_command_with_side_effects(self):
        """Test that commands with side effects work correctly."""
        cli = SimpleCLI("test", "Test CLI")
        state = {"value": 0}
        
        @cli.command("increment", "Increment value")
        def increment():
            state["value"] += 1
        
        @cli.command("double", "Double value")
        def double():
            state["value"] *= 2
        
        cli.run(["increment"])
        cli.run(["double"])
        cli.run(["increment"])
        
        assert state["value"] == 3  # (0 + 1) * 2 + 1
    
    def test_cli_with_no_arguments_shows_help(self):
        """Test that running CLI with no arguments shows help."""
        cli = SimpleCLI("test", "Test CLI")
        
        @cli.command("cmd", "Command")
        def cmd():
            pass
        
        with patch('builtins.print') as mock_print:
            cli.run([])
        
        printed_text = ' '.join(str(call) for call in mock_print.call_args_list)
        assert "Available commands" in printed_text

