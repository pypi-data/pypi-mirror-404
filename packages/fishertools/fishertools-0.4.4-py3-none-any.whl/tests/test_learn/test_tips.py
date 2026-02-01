"""
Unit tests for the tips module in fishertools.learn.

Tests the show_best_practice function and related utilities for
displaying Python best practices.
"""

import pytest
from io import StringIO
import sys
from fishertools.learn.tips import (
    show_best_practice,
    list_available_topics,
    get_topic_summary,
    BEST_PRACTICES
)


class TestShowBestPractice:
    """Test the show_best_practice function."""
    
    def capture_output(self, func, *args, **kwargs):
        """Helper method to capture print output."""
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        try:
            func(*args, **kwargs)
            return captured_output.getvalue()
        finally:
            sys.stdout = old_stdout
    
    def test_show_valid_topic(self):
        """Test showing best practices for a valid topic."""
        output = self.capture_output(show_best_practice, "variables")
        
        # Should contain expected sections
        assert "Переменные в Python" in output
        assert "ЛУЧШИЕ ПРАКТИКИ:" in output
        assert "ПРИМЕР КОДА:" in output
        
        # Should contain practical advice
        assert "snake_case" in output
        assert "описательные имена" in output
        
        # Should contain code examples
        assert "age = " in output or "name = " in output
    
    def test_show_invalid_topic(self):
        """Test showing best practices for an invalid topic."""
        output = self.capture_output(show_best_practice, "nonexistent_topic")
        
        # Should show error message
        assert "❌ Тема 'nonexistent_topic' не найдена" in output
        assert "📚 Доступные темы:" in output
    
    def test_case_insensitive_topic(self):
        """Test that topic matching is case insensitive."""
        output1 = self.capture_output(show_best_practice, "VARIABLES")
        output2 = self.capture_output(show_best_practice, "variables")
        
        # Both should show the same content
        assert "Переменные в Python" in output1
        assert "Переменные в Python" in output2
    
    def test_whitespace_handling(self):
        """Test that whitespace is handled correctly."""
        output = self.capture_output(show_best_practice, "  variables  ")
        
        # Should work despite extra whitespace
        assert "Переменные в Python" in output
    
    def test_all_topics_display_correctly(self):
        """Test that all available topics display correctly."""
        topics = list_available_topics()
        
        for topic in topics:
            output = self.capture_output(show_best_practice, topic)
            
            # Each should produce valid output
            assert len(output) > 100  # Should be substantial content
            assert "ЛУЧШИЕ ПРАКТИКИ:" in output
            assert "ПРИМЕР КОДА:" in output
            
            # Should not contain error messages (but may contain ❌ in educational content)
            assert "не найдена" not in output
            assert "Доступные темы:" not in output


class TestListAvailableTopics:
    """Test the list_available_topics function."""
    
    def test_returns_list(self):
        """Test that function returns a list."""
        result = list_available_topics()
        assert isinstance(result, list)
    
    def test_contains_expected_topics(self):
        """Test that list contains expected topics."""
        topics = list_available_topics()
        
        # Should contain core Python topics
        expected_topics = [
            "variables", "functions", "lists", 
            "dictionaries", "error_handling"
        ]
        
        for topic in expected_topics:
            assert topic in topics
    
    def test_all_topics_have_data(self):
        """Test that all listed topics have corresponding data."""
        topics = list_available_topics()
        
        for topic in topics:
            assert topic in BEST_PRACTICES
            assert "title" in BEST_PRACTICES[topic]
            assert "practices" in BEST_PRACTICES[topic]
            assert "example" in BEST_PRACTICES[topic]


class TestGetTopicSummary:
    """Test the get_topic_summary function."""
    
    def test_valid_topic_returns_summary(self):
        """Test getting summary for a valid topic."""
        summary = get_topic_summary("variables")
        
        assert isinstance(summary, str)
        assert len(summary) > 0
        assert "Переменные в Python" in summary
    
    def test_invalid_topic_returns_error(self):
        """Test getting summary for an invalid topic."""
        summary = get_topic_summary("nonexistent")
        assert "не найдена" in summary
    
    def test_case_insensitive_lookup(self):
        """Test that topic lookup is case insensitive."""
        summary1 = get_topic_summary("VARIABLES")
        summary2 = get_topic_summary("variables")
        
        assert summary1 == summary2
        assert "Переменные в Python" in summary1
    
    def test_whitespace_handling(self):
        """Test that whitespace is handled in topic lookup."""
        summary = get_topic_summary("  variables  ")
        
        assert "Переменные в Python" in summary


class TestBestPracticesData:
    """Test the BEST_PRACTICES data structure."""
    
    def test_all_practices_have_required_fields(self):
        """Test that all best practices have required fields."""
        for topic, data in BEST_PRACTICES.items():
            assert "title" in data
            assert "practices" in data
            assert "example" in data
            
            # Fields should not be empty
            assert len(data["title"]) > 0
            assert len(data["practices"]) > 0
            assert len(data["example"]) > 0
    
    def test_practices_contain_educational_content(self):
        """Test that practices contain educational content."""
        for topic, data in BEST_PRACTICES.items():
            practices = data["practices"]
            
            # Should contain visual indicators
            assert "🔹" in practices or "✅" in practices or "❌" in practices
            
            # Should contain Russian explanations
            assert any(char in practices for char in "абвгдеёжзийклмнопрстуфхцчшщъыьэюя")
    
    def test_examples_contain_actual_code(self):
        """Test that examples contain actual Python code."""
        for topic, data in BEST_PRACTICES.items():
            example = data["example"]
            
            # Should contain Python-like syntax
            assert any(keyword in example for keyword in ["def ", "=", "print(", "if ", "for "])
    
    def test_examples_are_educational(self):
        """Test that examples contain educational content."""
        for topic, data in BEST_PRACTICES.items():
            example = data["example"]
            
            # Should contain comments (educational explanations)
            assert "#" in example or '"""' in example
            
            # Should contain Russian explanations in comments or strings
            assert any(char in example for char in "абвгдеёжзийклмнопрстуфхцчшщъыьэюя")


class TestContentQuality:
    """Test the quality and accuracy of educational content."""
    
    def test_variables_topic_content(self):
        """Test specific content for variables topic."""
        data = BEST_PRACTICES["variables"]
        
        # Should mention key concepts
        assert "snake_case" in data["practices"]
        assert "описательные имена" in data["practices"]
        assert "константы" in data["practices"]
        
        # Example should demonstrate good practices
        example = data["example"]
        assert "user_name" in example or "first_name" in example  # snake_case
        assert "MAX_" in example  # constants
    
    def test_functions_topic_content(self):
        """Test specific content for functions topic."""
        data = BEST_PRACTICES["functions"]
        
        # Should mention key concepts
        assert "docstring" in data["practices"]
        assert "type hints" in data["practices"]
        
        # Example should demonstrate good practices
        example = data["example"]
        assert '"""' in example  # docstring
        assert "->" in example or ":" in example  # type hints or parameters
    
    def test_error_handling_topic_content(self):
        """Test specific content for error handling topic."""
        data = BEST_PRACTICES["error_handling"]
        
        # Should mention key concepts
        assert "try" in data["practices"] or "except" in data["practices"]
        assert "finally" in data["practices"] or "контекстные менеджеры" in data["practices"]
        
        # Example should demonstrate error handling
        example = data["example"]
        assert "try:" in example
        assert "except" in example


class TestIntegration:
    """Integration tests for the tips module."""
    
    def test_complete_workflow(self):
        """Test complete workflow of discovering and showing best practices."""
        # Get available topics
        topics = list_available_topics()
        assert len(topics) > 0
        
        # Get summary for first topic
        first_topic = topics[0]
        summary = get_topic_summary(first_topic)
        assert "не найдена" not in summary
        
        # Show best practices for the topic
        output = self.capture_output(show_best_practice, first_topic)
        assert "не найдена" not in output  # Should not be an error
        assert summary in output  # Should contain the title
    
    def test_error_handling_consistency(self):
        """Test that error handling is consistent across functions."""
        invalid_topic = "definitely_not_a_topic"
        
        # show_best_practice should display error message
        output = self.capture_output(show_best_practice, invalid_topic)
        assert "❌" in output
        
        # get_topic_summary should return error message
        summary = get_topic_summary(invalid_topic)
        assert "не найдена" in summary
        
        # list_available_topics should not include invalid topic
        topics = list_available_topics()
        assert invalid_topic not in topics
    
    def capture_output(self, func, *args, **kwargs):
        """Helper method to capture print output."""
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        try:
            func(*args, **kwargs)
            return captured_output.getvalue()
        finally:
            sys.stdout = old_stdout