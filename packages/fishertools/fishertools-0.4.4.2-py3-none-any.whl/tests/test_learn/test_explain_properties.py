"""
Property-based tests for the explain() function in fishertools.learn.

Tests the correctness properties of the explain() function using hypothesis
for property-based testing.

**Validates: Requirements 1.1, 1.2, 1.6**
"""

import pytest
from hypothesis import given, strategies as st, assume
import json
import os

from fishertools.learn.examples import explain


# Get the list of valid topics from the explanations.json file
def get_valid_topics():
    """Get all valid topics from explanations.json."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    explanations_path = os.path.join(
        current_dir, '..', '..', 'fishertools', 'learn', 'explanations.json'
    )
    
    with open(explanations_path, 'r', encoding='utf-8') as f:
        explanations = json.load(f)
    
    return sorted(explanations.keys())


VALID_TOPICS = get_valid_topics()

# Define the required topics from the specification
REQUIRED_TOPICS = {
    'int', 'float', 'str', 'bool', 'list', 'tuple', 'set', 'dict',
    'if', 'for', 'while', 'break', 'continue',
    'function', 'return', 'lambda', '*args', '**kwargs',
    'try', 'except', 'finally', 'raise',
    'open', 'read', 'write', 'with'
}


class TestExplainReturnsValidStructure:
    """
    Property 1: Explain Returns Valid Structure
    
    For any valid topic name, calling explain(topic) should return a dictionary
    containing exactly the keys: description, when_to_use, and example, with all
    values being non-empty strings.
    
    **Validates: Requirements 1.1, 1.3, 1.4, 1.5**
    """
    
    @given(st.sampled_from(VALID_TOPICS))
    def test_explain_returns_dict_with_correct_keys(self, topic):
        """Test that explain() returns a dict with the correct keys."""
        result = explain(topic)
        
        # Should return a dictionary
        assert isinstance(result, dict)
        
        # Should have exactly the required keys
        expected_keys = {'description', 'when_to_use', 'example'}
        assert set(result.keys()) == expected_keys
    
    @given(st.sampled_from(VALID_TOPICS))
    def test_explain_returns_non_empty_strings(self, topic):
        """Test that all values in the returned dict are non-empty strings."""
        result = explain(topic)
        
        # All values should be strings
        assert isinstance(result['description'], str)
        assert isinstance(result['when_to_use'], str)
        assert isinstance(result['example'], str)
        
        # All values should be non-empty
        assert len(result['description']) > 0
        assert len(result['when_to_use']) > 0
        assert len(result['example']) > 0
    
    @given(st.sampled_from(VALID_TOPICS))
    def test_explain_description_is_meaningful(self, topic):
        """Test that description contains meaningful content."""
        result = explain(topic)
        description = result['description']
        
        # Description should be at least 20 characters
        assert len(description) >= 20
        
        # Description should contain alphabetic characters
        assert any(c.isalpha() for c in description)
    
    @given(st.sampled_from(VALID_TOPICS))
    def test_explain_when_to_use_is_meaningful(self, topic):
        """Test that when_to_use contains meaningful content."""
        result = explain(topic)
        when_to_use = result['when_to_use']
        
        # when_to_use should be at least 20 characters
        assert len(when_to_use) >= 20
        
        # when_to_use should contain alphabetic characters
        assert any(c.isalpha() for c in when_to_use)
    
    @given(st.sampled_from(VALID_TOPICS))
    def test_explain_example_is_code(self, topic):
        """Test that example contains code-like content."""
        result = explain(topic)
        example = result['example']
        
        # Example should be at least 10 characters
        assert len(example) >= 10
        
        # Example should contain code-like patterns (=, (), etc.)
        code_indicators = ['=', '(', ')', '[', ']', '{', '}', 'print', 'def', 'if', 'for']
        assert any(indicator in example for indicator in code_indicators)
    
    @given(st.sampled_from(VALID_TOPICS))
    def test_explain_case_insensitive(self, topic):
        """Test that explain() is case insensitive."""
        result_lower = explain(topic.lower())
        result_upper = explain(topic.upper())
        result_mixed = explain(topic.capitalize())
        
        # All should return the same result
        assert result_lower == result_upper
        assert result_lower == result_mixed


class TestExplainRejectsInvalidTopics:
    """
    Property 2: Explain Rejects Invalid Topics
    
    For any invalid topic name, calling explain(topic) should raise a ValueError
    exception.
    
    **Validates: Requirements 1.2**
    """
    
    @given(st.text(min_size=1))
    def test_explain_raises_valueerror_for_invalid_topics(self, topic):
        """Test that explain() raises ValueError for invalid topics."""
        # Skip if the topic happens to be valid (after normalization)
        assume(topic.lower().strip() not in VALID_TOPICS)
        
        # Should raise ValueError
        with pytest.raises(ValueError):
            explain(topic)
    
    @given(st.text(min_size=1))
    def test_explain_error_message_lists_available_topics(self, topic):
        """Test that ValueError message lists available topics."""
        # Skip if the topic happens to be valid (after normalization)
        assume(topic.lower().strip() not in VALID_TOPICS)
        
        try:
            explain(topic)
            pytest.fail("Should have raised ValueError")
        except ValueError as e:
            error_msg = str(e)
            
            # Error message should mention available topics
            assert "Available topics" in error_msg or "available topics" in error_msg.lower()
            
            # Error message should contain at least one valid topic
            assert any(valid_topic in error_msg for valid_topic in VALID_TOPICS)
    
    def test_explain_rejects_empty_string(self):
        """Test that explain() rejects empty string."""
        with pytest.raises(ValueError):
            explain("")
    
    def test_explain_rejects_whitespace_only(self):
        """Test that explain() rejects whitespace-only strings."""
        with pytest.raises(ValueError):
            explain("   ")
    
    def test_explain_rejects_special_characters(self):
        """Test that explain() rejects topics with only special characters."""
        with pytest.raises(ValueError):
            explain("!@#$%^&*()")


class TestExplainAllRequiredTopicsAvailable:
    """
    Property 3: All Required Topics Available
    
    For all required topics (int, float, str, bool, list, tuple, set, dict, if,
    for, while, break, continue, function, return, lambda, *args, **kwargs, try,
    except, finally, raise, open, read, write, with), calling explain(topic)
    should succeed and return a valid explanation.
    
    **Validates: Requirements 1.6, 2.1, 3.1, 4.1, 5.1, 6.1**
    """
    
    @given(st.sampled_from(sorted(REQUIRED_TOPICS)))
    def test_all_required_topics_available(self, topic):
        """Test that all required topics are available."""
        # Should not raise an exception
        result = explain(topic)
        
        # Should return valid structure
        assert isinstance(result, dict)
        assert set(result.keys()) == {'description', 'when_to_use', 'example'}
        assert all(isinstance(v, str) and len(v) > 0 for v in result.values())
    
    def test_all_required_topics_explicitly(self):
        """Test all required topics explicitly."""
        for topic in REQUIRED_TOPICS:
            result = explain(topic)
            
            # Verify structure
            assert isinstance(result, dict)
            assert 'description' in result
            assert 'when_to_use' in result
            assert 'example' in result
            
            # Verify non-empty values
            assert len(result['description']) > 0
            assert len(result['when_to_use']) > 0
            assert len(result['example']) > 0
    
    def test_required_topics_count(self):
        """Test that all required topics are present."""
        available_topics = set(VALID_TOPICS)
        
        # All required topics should be available
        missing_topics = REQUIRED_TOPICS - available_topics
        assert len(missing_topics) == 0, f"Missing topics: {missing_topics}"
    
    def test_required_topics_have_meaningful_content(self):
        """Test that required topics have meaningful explanations."""
        for topic in REQUIRED_TOPICS:
            result = explain(topic)
            
            # Each field should have substantial content
            assert len(result['description']) >= 20
            assert len(result['when_to_use']) >= 20
            assert len(result['example']) >= 10


class TestExplainEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_explain_with_leading_trailing_whitespace(self):
        """Test that explain() handles leading/trailing whitespace."""
        result1 = explain("list")
        result2 = explain("  list  ")
        result3 = explain("\tlist\n")
        
        # All should return the same result
        assert result1 == result2
        assert result1 == result3
    
    def test_explain_consistency_across_calls(self):
        """Test that explain() returns consistent results across multiple calls."""
        result1 = explain("dict")
        result2 = explain("dict")
        result3 = explain("dict")
        
        # All calls should return identical results
        assert result1 == result2
        assert result2 == result3
    
    @given(st.sampled_from(VALID_TOPICS))
    def test_explain_result_is_independent(self, topic):
        """Test that modifying returned dict doesn't affect future calls."""
        result1 = explain(topic)
        
        # Modify the returned dict
        result1['description'] = "MODIFIED"
        result1['new_key'] = "NEW VALUE"
        
        # Next call should return unmodified result
        result2 = explain(topic)
        assert result2['description'] != "MODIFIED"
        assert 'new_key' not in result2


class TestExplainIntegration:
    """Integration tests for explain() function."""
    
    def test_explain_with_all_valid_topics(self):
        """Test explain() with all valid topics."""
        for topic in VALID_TOPICS:
            result = explain(topic)
            
            # Should return valid structure
            assert isinstance(result, dict)
            assert set(result.keys()) == {'description', 'when_to_use', 'example'}
            assert all(isinstance(v, str) and len(v) > 0 for v in result.values())
    
    def test_explain_error_message_quality(self):
        """Test that error messages are helpful."""
        try:
            explain("nonexistent_topic_xyz")
            pytest.fail("Should have raised ValueError")
        except ValueError as e:
            error_msg = str(e)
            
            # Error message should be informative
            assert "nonexistent_topic_xyz" in error_msg
            assert "Available topics" in error_msg or "available" in error_msg.lower()
            
            # Should list some topics
            assert len(error_msg) > 50  # Substantial message
