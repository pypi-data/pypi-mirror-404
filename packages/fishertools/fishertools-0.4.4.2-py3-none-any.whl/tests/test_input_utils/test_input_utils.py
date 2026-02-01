"""Unit tests for the input_utils module."""

import pytest
from fishertools.input_utils import ask_int, ask_float, ask_str, ask_choice


class TestAskInt:
    """Tests for ask_int function."""
    
    def test_ask_int_basic(self, monkeypatch):
        """Test basic integer input."""
        monkeypatch.setattr('builtins.input', lambda _: '42')
        result = ask_int("Enter a number: ")
        assert result == 42
        assert isinstance(result, int)
    
    def test_ask_int_with_min_max(self, monkeypatch):
        """Test integer input with min/max constraints."""
        monkeypatch.setattr('builtins.input', lambda _: '50')
        result = ask_int("Enter a number: ", min_val=0, max_val=100)
        assert result == 50


class TestAskFloat:
    """Tests for ask_float function."""
    
    def test_ask_float_basic(self, monkeypatch):
        """Test basic float input."""
        monkeypatch.setattr('builtins.input', lambda _: '3.14')
        result = ask_float("Enter a number: ")
        assert abs(result - 3.14) < 1e-9
        assert isinstance(result, float)


class TestAskStr:
    """Tests for ask_str function."""
    
    def test_ask_str_basic(self, monkeypatch):
        """Test basic string input."""
        monkeypatch.setattr('builtins.input', lambda _: 'hello')
        result = ask_str("Enter text: ")
        assert result == 'hello'
        assert isinstance(result, str)
    
    def test_ask_str_strips_whitespace(self, monkeypatch):
        """Test that whitespace is stripped from string input."""
        monkeypatch.setattr('builtins.input', lambda _: '  hello  ')
        result = ask_str("Enter text: ")
        assert result == 'hello'


class TestAskChoice:
    """Tests for ask_choice function."""
    
    def test_ask_choice_basic(self, monkeypatch):
        """Test basic choice selection."""
        monkeypatch.setattr('builtins.input', lambda _: 'red')
        result = ask_choice("Choose a color: ", ['red', 'green', 'blue'])
        assert result == 'red'
    
    def test_ask_choice_numeric(self, monkeypatch):
        """Test numeric choice selection."""
        monkeypatch.setattr('builtins.input', lambda _: '1')
        result = ask_choice("Choose a color: ", ['red', 'green', 'blue'])
        assert result == 'red'
