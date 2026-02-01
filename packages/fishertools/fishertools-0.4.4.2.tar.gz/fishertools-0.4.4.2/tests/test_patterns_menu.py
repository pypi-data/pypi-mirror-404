"""
Property-based tests for the simple_menu() function in fishertools.patterns.

Tests the correctness properties of the simple_menu() function using hypothesis
for property-based testing.

**Validates: Requirements 8.1, 8.3, 8.4**
"""

import pytest
from hypothesis import given, strategies as st, assume
from unittest.mock import patch, MagicMock
from io import StringIO

from fishertools.patterns.menu import simple_menu


class TestSimpleMenuAcceptsDictionary:
    """
    Property 11: Simple Menu Accepts Dictionary
    
    For any dictionary of options, simple_menu should accept it and process
    valid selections.
    
    **Validates: Requirements 8.1, 8.3**
    """
    
    def test_simple_menu_accepts_valid_dict(self):
        """Test that simple_menu accepts a valid dictionary."""
        def func1():
            return "func1"
        
        def func2():
            return "func2"
        
        options = {
            "Option 1": func1,
            "Option 2": func2
        }
        
        # Should not raise an exception when given valid input
        with patch('builtins.input', return_value='quit'):
            simple_menu(options)
    
    def test_simple_menu_displays_menu_options(self):
        """Test that simple_menu displays all menu options."""
        def func1():
            pass
        
        def func2():
            pass
        
        options = {
            "First Option": func1,
            "Second Option": func2
        }
        
        with patch('builtins.input', return_value='quit'):
            with patch('builtins.print') as mock_print:
                simple_menu(options)
                
                # Check that menu options were printed
                printed_text = ' '.join(str(call) for call in mock_print.call_args_list)
                assert "First Option" in printed_text
                assert "Second Option" in printed_text
    
    def test_simple_menu_executes_selected_function(self):
        """Test that simple_menu executes the selected function."""
        mock_func1 = MagicMock()
        mock_func2 = MagicMock()
        
        options = {
            "Option 1": mock_func1,
            "Option 2": mock_func2
        }
        
        # Select option 1, then quit
        with patch('builtins.input', side_effect=['1', 'quit']):
            simple_menu(options)
        
        # Option 1 should have been called
        mock_func1.assert_called_once()
        mock_func2.assert_not_called()
    
    def test_simple_menu_executes_correct_function_for_each_option(self):
        """Test that simple_menu executes the correct function for each option."""
        mock_func1 = MagicMock()
        mock_func2 = MagicMock()
        mock_func3 = MagicMock()
        
        options = {
            "Option 1": mock_func1,
            "Option 2": mock_func2,
            "Option 3": mock_func3
        }
        
        # Select option 2, then quit
        with patch('builtins.input', side_effect=['2', 'quit']):
            simple_menu(options)
        
        # Only option 2 should have been called
        mock_func1.assert_not_called()
        mock_func2.assert_called_once()
        mock_func3.assert_not_called()
    
    def test_simple_menu_with_single_option(self):
        """Test that simple_menu works with a single option."""
        mock_func = MagicMock()
        
        options = {"Only Option": mock_func}
        
        with patch('builtins.input', side_effect=['1', 'quit']):
            simple_menu(options)
        
        mock_func.assert_called_once()
    
    def test_simple_menu_with_many_options(self):
        """Test that simple_menu works with many options."""
        funcs = [MagicMock() for _ in range(10)]
        options = {f"Option {i+1}": func for i, func in enumerate(funcs)}
        
        # Select option 5, then quit
        with patch('builtins.input', side_effect=['5', 'quit']):
            simple_menu(options)
        
        # Only option 5 should have been called
        for i, func in enumerate(funcs):
            if i == 4:  # 0-indexed, so option 5 is index 4
                func.assert_called_once()
            else:
                func.assert_not_called()
    
    def test_simple_menu_preserves_option_order(self):
        """Test that simple_menu preserves the order of options."""
        funcs = [MagicMock() for _ in range(3)]
        options = {
            "First": funcs[0],
            "Second": funcs[1],
            "Third": funcs[2]
        }
        
        with patch('builtins.input', return_value='quit'):
            with patch('builtins.print') as mock_print:
                simple_menu(options)
                
                # Get all printed output
                printed_text = ' '.join(str(call) for call in mock_print.call_args_list)
                
                # Check that options appear in order
                first_pos = printed_text.find("First")
                second_pos = printed_text.find("Second")
                third_pos = printed_text.find("Third")
                
                assert first_pos < second_pos < third_pos


class TestSimpleMenuRejectsInvalidOptions:
    """
    Property 12: Simple Menu Rejects Invalid Options
    
    For any invalid menu selection, simple_menu should display an error and
    re-prompt.
    
    **Validates: Requirements 8.4**
    """
    
    def test_simple_menu_rejects_out_of_range_number(self):
        """Test that simple_menu rejects out-of-range numbers."""
        mock_func = MagicMock()
        options = {"Option 1": mock_func}
        
        # Try option 5 (out of range), then quit
        with patch('builtins.input', side_effect=['5', 'quit']):
            with patch('builtins.print') as mock_print:
                simple_menu(options)
                
                # Should print an error message
                printed_text = ' '.join(str(call) for call in mock_print.call_args_list)
                assert "Error" in printed_text or "error" in printed_text.lower()
        
        # Function should not have been called
        mock_func.assert_not_called()
    
    def test_simple_menu_rejects_negative_number(self):
        """Test that simple_menu rejects negative numbers."""
        mock_func = MagicMock()
        options = {"Option 1": mock_func}
        
        # Try negative number, then quit
        with patch('builtins.input', side_effect=['-1', 'quit']):
            with patch('builtins.print') as mock_print:
                simple_menu(options)
                
                # Should print an error message
                printed_text = ' '.join(str(call) for call in mock_print.call_args_list)
                assert "Error" in printed_text or "error" in printed_text.lower()
        
        # Function should not have been called
        mock_func.assert_not_called()
    
    def test_simple_menu_rejects_non_numeric_input(self):
        """Test that simple_menu rejects non-numeric input."""
        mock_func = MagicMock()
        options = {"Option 1": mock_func}
        
        # Try non-numeric input, then quit
        with patch('builtins.input', side_effect=['abc', 'quit']):
            with patch('builtins.print') as mock_print:
                simple_menu(options)
                
                # Should print an error message
                printed_text = ' '.join(str(call) for call in mock_print.call_args_list)
                assert "Error" in printed_text or "error" in printed_text.lower()
        
        # Function should not have been called
        mock_func.assert_not_called()
    
    def test_simple_menu_rejects_zero(self):
        """Test that simple_menu rejects zero as a selection."""
        mock_func = MagicMock()
        options = {"Option 1": mock_func}
        
        # Try zero, then quit
        with patch('builtins.input', side_effect=['0', 'quit']):
            with patch('builtins.print') as mock_print:
                simple_menu(options)
                
                # Should print an error message
                printed_text = ' '.join(str(call) for call in mock_print.call_args_list)
                assert "Error" in printed_text or "error" in printed_text.lower()
        
        # Function should not have been called
        mock_func.assert_not_called()
    
    def test_simple_menu_reprompts_after_invalid_input(self):
        """Test that simple_menu re-prompts after invalid input."""
        mock_func = MagicMock()
        options = {"Option 1": mock_func}
        
        # Try invalid input, then valid input, then quit
        with patch('builtins.input', side_effect=['invalid', '1', 'quit']):
            simple_menu(options)
        
        # Function should have been called after valid input
        mock_func.assert_called_once()
    
    def test_simple_menu_handles_multiple_invalid_inputs(self):
        """Test that simple_menu handles multiple invalid inputs."""
        mock_func = MagicMock()
        options = {"Option 1": mock_func}
        
        # Try multiple invalid inputs, then valid input, then quit
        with patch('builtins.input', side_effect=['abc', '5', '-1', '1', 'quit']):
            simple_menu(options)
        
        # Function should have been called once after valid input
        mock_func.assert_called_once()
    
    def test_simple_menu_rejects_float_input(self):
        """Test that simple_menu rejects float input."""
        mock_func = MagicMock()
        options = {"Option 1": mock_func}
        
        # Try float input, then quit
        with patch('builtins.input', side_effect=['1.5', 'quit']):
            with patch('builtins.print') as mock_print:
                simple_menu(options)
                
                # Should print an error message
                printed_text = ' '.join(str(call) for call in mock_print.call_args_list)
                assert "Error" in printed_text or "error" in printed_text.lower()
        
        # Function should not have been called
        mock_func.assert_not_called()


class TestSimpleMenuExitHandling:
    """Test exit/quit command handling."""
    
    def test_simple_menu_exits_on_quit(self):
        """Test that simple_menu exits on 'quit' command."""
        mock_func = MagicMock()
        options = {"Option 1": mock_func}
        
        with patch('builtins.input', return_value='quit'):
            simple_menu(options)
        
        # Function should not have been called
        mock_func.assert_not_called()
    
    def test_simple_menu_exits_on_exit(self):
        """Test that simple_menu exits on 'exit' command."""
        mock_func = MagicMock()
        options = {"Option 1": mock_func}
        
        with patch('builtins.input', return_value='exit'):
            simple_menu(options)
        
        # Function should not have been called
        mock_func.assert_not_called()
    
    def test_simple_menu_exits_on_quit_uppercase(self):
        """Test that simple_menu exits on 'QUIT' command."""
        mock_func = MagicMock()
        options = {"Option 1": mock_func}
        
        with patch('builtins.input', return_value='QUIT'):
            simple_menu(options)
        
        # Function should not have been called
        mock_func.assert_not_called()
    
    def test_simple_menu_exits_on_exit_uppercase(self):
        """Test that simple_menu exits on 'EXIT' command."""
        mock_func = MagicMock()
        options = {"Option 1": mock_func}
        
        with patch('builtins.input', return_value='EXIT'):
            simple_menu(options)
        
        # Function should not have been called
        mock_func.assert_not_called()
    
    def test_simple_menu_exits_on_quit_with_whitespace(self):
        """Test that simple_menu exits on 'quit' with whitespace."""
        mock_func = MagicMock()
        options = {"Option 1": mock_func}
        
        with patch('builtins.input', return_value='  quit  '):
            simple_menu(options)
        
        # Function should not have been called
        mock_func.assert_not_called()


class TestSimpleMenuErrorHandling:
    """Test error handling in simple_menu."""
    
    def test_simple_menu_raises_typeerror_for_non_dict(self):
        """Test that simple_menu raises TypeError for non-dict input."""
        with pytest.raises(TypeError):
            simple_menu([("Option 1", lambda: None)])
    
    def test_simple_menu_raises_typeerror_for_non_callable_values(self):
        """Test that simple_menu raises TypeError for non-callable values."""
        with pytest.raises(TypeError):
            simple_menu({"Option 1": "not a function"})
    
    def test_simple_menu_raises_valueerror_for_empty_dict(self):
        """Test that simple_menu raises ValueError for empty dictionary."""
        with pytest.raises(ValueError):
            simple_menu({})
    
    def test_simple_menu_raises_typeerror_for_none(self):
        """Test that simple_menu raises TypeError for None input."""
        with pytest.raises(TypeError):
            simple_menu(None)
    
    def test_simple_menu_raises_typeerror_for_string(self):
        """Test that simple_menu raises TypeError for string input."""
        with pytest.raises(TypeError):
            simple_menu("not a dict")


class TestSimpleMenuIntegration:
    """Integration tests for simple_menu."""
    
    def test_simple_menu_full_workflow(self):
        """Test a complete workflow with simple_menu."""
        results = []
        
        def option1():
            results.append("option1")
        
        def option2():
            results.append("option2")
        
        options = {
            "First": option1,
            "Second": option2
        }
        
        # Select option 1, then option 2, then quit
        with patch('builtins.input', side_effect=['1', '2', 'quit']):
            simple_menu(options)
        
        # Both functions should have been called in order
        assert results == ["option1", "option2"]
    
    def test_simple_menu_with_exception_in_function(self):
        """Test that simple_menu handles exceptions in selected functions."""
        def failing_func():
            raise ValueError("Test error")
        
        def working_func():
            pass
        
        options = {
            "Failing": failing_func,
            "Working": working_func
        }
        
        # Select failing function, then working function, then quit
        # The ValueError from failing_func will be caught and treated as invalid input
        with patch('builtins.input', side_effect=['1', '2', 'quit']):
            simple_menu(options)
    
    def test_simple_menu_displays_numbered_options(self):
        """Test that simple_menu displays options with numbers."""
        options = {
            "Option A": lambda: None,
            "Option B": lambda: None,
            "Option C": lambda: None
        }
        
        with patch('builtins.input', return_value='quit'):
            with patch('builtins.print') as mock_print:
                simple_menu(options)
                
                # Get all printed output
                printed_text = ' '.join(str(call) for call in mock_print.call_args_list)
                
                # Should contain numbered options
                assert "1" in printed_text
                assert "2" in printed_text
                assert "3" in printed_text
    
    def test_simple_menu_with_special_characters_in_option_names(self):
        """Test that simple_menu handles special characters in option names."""
        mock_func = MagicMock()
        options = {
            "Option with spaces": mock_func,
            "Option-with-dashes": mock_func,
            "Option_with_underscores": mock_func
        }
        
        with patch('builtins.input', side_effect=['1', 'quit']):
            simple_menu(options)
        
        mock_func.assert_called_once()
