"""
Property-based tests for CommandParser using Hypothesis.

**Validates: Requirements 1.2, 1.3**
"""

import pytest
from hypothesis import given, strategies as st, assume
from fishertools.learn.repl.command_parser import CommandParser


class TestCommandParserProperties:
    """Property-based tests for command parsing consistency."""
    
    @given(st.text(min_size=1))
    def test_parse_consistency(self, input_str):
        """
        Property 1: Command Parsing Consistency
        
        For any user input string, parsing it should consistently identify 
        the same command type and arguments across multiple invocations.
        
        **Validates: Requirements 1.2, 1.3**
        """
        # Skip empty or whitespace-only strings
        if not input_str or not input_str.strip():
            return
        
        try:
            # Parse the same input twice
            result1 = CommandParser.parse(input_str)
            result2 = CommandParser.parse(input_str)
            
            # Results should be identical
            assert result1 == result2, f"Parsing inconsistent for input: {input_str}"
        except ValueError:
            # If parsing fails, it should fail consistently
            with pytest.raises(ValueError):
                CommandParser.parse(input_str)
    
    @given(st.text(min_size=1, max_size=100))
    def test_command_type_is_valid(self, input_str):
        """
        For any valid input, the command type should be one of the valid types.
        
        **Validates: Requirements 1.2, 1.3**
        """
        if not input_str or not input_str.strip():
            return
        
        try:
            cmd_type, args = CommandParser.parse(input_str)
            assert cmd_type in ["command", "topic"], f"Invalid command type: {cmd_type}"
            assert isinstance(args, list), "Arguments should be a list"
            assert len(args) > 0, "Arguments list should not be empty"
        except ValueError:
            # Invalid input is acceptable
            pass
    
    @given(st.text(min_size=1))
    def test_parse_returns_tuple(self, input_str):
        """
        For any valid input, parse should return a tuple of (str, list).
        
        **Validates: Requirements 1.2, 1.3**
        """
        if not input_str or not input_str.strip():
            return
        
        try:
            result = CommandParser.parse(input_str)
            assert isinstance(result, tuple), "Result should be a tuple"
            assert len(result) == 2, "Result should have 2 elements"
            assert isinstance(result[0], str), "First element should be string"
            assert isinstance(result[1], list), "Second element should be list"
        except ValueError:
            # Invalid input is acceptable
            pass
    
    @given(st.text(min_size=1))
    def test_command_parsing_idempotent(self, input_str):
        """
        For any input that parses successfully, parsing it multiple times 
        should always produce the same result.
        
        **Validates: Requirements 1.2, 1.3**
        """
        if not input_str or not input_str.strip():
            return
        
        try:
            results = [CommandParser.parse(input_str) for _ in range(3)]
            # All results should be identical
            assert all(r == results[0] for r in results), \
                f"Parsing not idempotent for: {input_str}"
        except ValueError:
            # If it fails once, it should always fail
            for _ in range(3):
                with pytest.raises(ValueError):
                    CommandParser.parse(input_str)
