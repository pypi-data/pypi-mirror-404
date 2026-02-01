"""
Unit tests for the examples module in fishertools.learn.

Tests the generate_example function and related utilities for
generating educational code examples.
"""

import pytest
from fishertools.learn.examples import (
    generate_example,
    list_available_concepts,
    get_concept_info,
    explain,
    CODE_EXAMPLES
)


class TestGenerateExample:
    """Test the generate_example function."""
    
    def test_generate_example_valid_concept(self):
        """Test generating example for a valid concept."""
        result = generate_example("variables")
        
        # Should return a formatted string with content
        assert isinstance(result, str)
        assert len(result) > 0
        
        # Should contain expected sections
        assert "Переменные и типы данных" in result
        assert "Описание:" in result
        assert "Пример кода:" in result
        assert "Совет:" in result
        
        # Should contain actual code content
        assert "name = " in result
        assert "print(" in result
    
    def test_generate_example_invalid_concept(self):
        """Test generating example for an invalid concept."""
        result = generate_example("nonexistent_concept")
        
        # Should return error message
        assert "❌ Концепция 'nonexistent_concept' не найдена" in result
        assert "📚 Доступные концепции:" in result
    
    def test_generate_example_case_insensitive(self):
        """Test that concept matching is case insensitive."""
        result1 = generate_example("VARIABLES")
        result2 = generate_example("variables")
        result3 = generate_example("Variables")
        
        # All should produce the same result
        assert "Переменные и типы данных" in result1
        assert "Переменные и типы данных" in result2
        assert "Переменные и типы данных" in result3
    
    def test_generate_example_whitespace_handling(self):
        """Test that whitespace is handled correctly."""
        result = generate_example("  variables  ")
        
        # Should work despite extra whitespace
        assert "Переменные и типы данных" in result
    
    def test_all_concepts_generate_valid_examples(self):
        """Test that all available concepts generate valid examples."""
        concepts = list_available_concepts()
        
        for concept in concepts:
            result = generate_example(concept)
            
            # Each should return a valid formatted example
            assert isinstance(result, str)
            assert len(result) > 100  # Should be substantial content
            assert "Описание:" in result
            assert "Пример кода:" in result
            assert "Совет:" in result
            
            # Should not contain error messages (but may contain ❌ in educational content)
            assert "не найдена" not in result
            assert "Доступные концепции:" not in result


class TestListAvailableConcepts:
    """Test the list_available_concepts function."""
    
    def test_returns_list(self):
        """Test that function returns a list."""
        result = list_available_concepts()
        assert isinstance(result, list)
    
    def test_contains_expected_concepts(self):
        """Test that list contains expected concepts."""
        concepts = list_available_concepts()
        
        # Should contain core Python concepts
        expected_concepts = [
            "variables", "lists", "dictionaries", 
            "functions", "loops", "conditionals", "file_operations"
        ]
        
        for concept in expected_concepts:
            assert concept in concepts
    
    def test_all_concepts_have_data(self):
        """Test that all listed concepts have corresponding data."""
        concepts = list_available_concepts()
        
        for concept in concepts:
            assert concept in CODE_EXAMPLES
            assert "title" in CODE_EXAMPLES[concept]
            assert "description" in CODE_EXAMPLES[concept]
            assert "code" in CODE_EXAMPLES[concept]


class TestGetConceptInfo:
    """Test the get_concept_info function."""
    
    def test_valid_concept_returns_info(self):
        """Test getting info for a valid concept."""
        info = get_concept_info("variables")
        
        assert info is not None
        assert isinstance(info, dict)
        assert "title" in info
        assert "description" in info
        
        # Should contain expected content
        assert "Переменные и типы данных" in info["title"]
        assert "Основы работы с переменными" in info["description"]
    
    def test_invalid_concept_returns_none(self):
        """Test getting info for an invalid concept."""
        info = get_concept_info("nonexistent")
        assert info is None
    
    def test_case_insensitive_lookup(self):
        """Test that concept lookup is case insensitive."""
        info1 = get_concept_info("VARIABLES")
        info2 = get_concept_info("variables")
        
        assert info1 is not None
        assert info2 is not None
        assert info1["title"] == info2["title"]
    
    def test_whitespace_handling(self):
        """Test that whitespace is handled in concept lookup."""
        info = get_concept_info("  variables  ")
        
        assert info is not None
        assert "Переменные и типы данных" in info["title"]


class TestCodeExamplesData:
    """Test the CODE_EXAMPLES data structure."""
    
    def test_all_examples_have_required_fields(self):
        """Test that all code examples have required fields."""
        for concept, data in CODE_EXAMPLES.items():
            assert "title" in data
            assert "description" in data
            assert "code" in data
            
            # Fields should not be empty
            assert len(data["title"]) > 0
            assert len(data["description"]) > 0
            assert len(data["code"]) > 0
    
    def test_code_examples_contain_actual_code(self):
        """Test that code examples contain actual Python code."""
        for concept, data in CODE_EXAMPLES.items():
            code = data["code"]
            
            # Should contain Python-like syntax
            assert any(keyword in code for keyword in ["print(", "def ", "=", "if ", "for "])
    
    def test_examples_are_educational(self):
        """Test that examples contain educational content."""
        for concept, data in CODE_EXAMPLES.items():
            code = data["code"]
            
            # Should contain comments (educational explanations)
            assert "#" in code
            
            # Should contain Russian explanations
            assert any(char in code for char in "абвгдеёжзийклмнопрстуфхцчшщъыьэюя")


class TestIntegration:
    """Integration tests for the examples module."""
    
    def test_complete_workflow(self):
        """Test complete workflow of discovering and generating examples."""
        # Get available concepts
        concepts = list_available_concepts()
        assert len(concepts) > 0
        
        # Get info for first concept
        first_concept = concepts[0]
        info = get_concept_info(first_concept)
        assert info is not None
        
        # Generate example for the concept
        example = generate_example(first_concept)
        assert "❌" not in example  # Should not be an error
        assert info["title"] in example  # Should contain the title
    
    def test_error_handling_consistency(self):
        """Test that error handling is consistent across functions."""
        invalid_concept = "definitely_not_a_concept"
        
        # generate_example should return error message
        example_result = generate_example(invalid_concept)
        assert "❌" in example_result
        
        # get_concept_info should return None
        info_result = get_concept_info(invalid_concept)
        assert info_result is None
        
        # list_available_concepts should not include invalid concept
        concepts = list_available_concepts()
        assert invalid_concept not in concepts



class TestExplain:
    """Test the explain() function."""
    
    def test_explain_valid_topic_returns_dict(self):
        """Test that explain() returns a dict for valid topics."""
        result = explain("list")
        
        assert isinstance(result, dict)
        assert len(result) > 0
    
    def test_explain_returns_required_keys(self):
        """Test that explain() returns all required keys."""
        result = explain("int")
        
        required_keys = {'description', 'when_to_use', 'example'}
        assert set(result.keys()) == required_keys
    
    def test_explain_all_values_are_strings(self):
        """Test that all values in explain() result are strings."""
        result = explain("dict")
        
        assert isinstance(result['description'], str)
        assert isinstance(result['when_to_use'], str)
        assert isinstance(result['example'], str)
    
    def test_explain_all_values_non_empty(self):
        """Test that all values in explain() result are non-empty."""
        result = explain("for")
        
        assert len(result['description']) > 0
        assert len(result['when_to_use']) > 0
        assert len(result['example']) > 0
    
    def test_explain_case_insensitive(self):
        """Test that explain() is case insensitive."""
        result_lower = explain("list")
        result_upper = explain("LIST")
        result_mixed = explain("List")
        
        assert result_lower == result_upper
        assert result_lower == result_mixed
    
    def test_explain_whitespace_handling(self):
        """Test that explain() handles whitespace correctly."""
        result1 = explain("list")
        result2 = explain("  list  ")
        result3 = explain("\tlist\n")
        
        assert result1 == result2
        assert result1 == result3
    
    def test_explain_invalid_topic_raises_valueerror(self):
        """Test that explain() raises ValueError for invalid topics."""
        with pytest.raises(ValueError):
            explain("invalid_topic_xyz")
    
    def test_explain_error_message_helpful(self):
        """Test that ValueError message is helpful."""
        try:
            explain("nonexistent")
            pytest.fail("Should have raised ValueError")
        except ValueError as e:
            error_msg = str(e)
            
            # Should mention the invalid topic
            assert "nonexistent" in error_msg
            
            # Should list available topics
            assert "Available topics" in error_msg or "available" in error_msg.lower()
    
    def test_explain_empty_string_raises_error(self):
        """Test that explain() raises error for empty string."""
        with pytest.raises(ValueError):
            explain("")
    
    def test_explain_whitespace_only_raises_error(self):
        """Test that explain() raises error for whitespace-only string."""
        with pytest.raises(ValueError):
            explain("   ")
    
    def test_explain_all_data_types(self):
        """Test explain() for all data type topics."""
        data_types = ['int', 'float', 'str', 'bool', 'list', 'tuple', 'set', 'dict']
        
        for dtype in data_types:
            result = explain(dtype)
            
            assert isinstance(result, dict)
            assert set(result.keys()) == {'description', 'when_to_use', 'example'}
            assert all(len(v) > 0 for v in result.values())
    
    def test_explain_all_control_structures(self):
        """Test explain() for all control structure topics."""
        control_structures = ['if', 'for', 'while', 'break', 'continue']
        
        for cs in control_structures:
            result = explain(cs)
            
            assert isinstance(result, dict)
            assert set(result.keys()) == {'description', 'when_to_use', 'example'}
            assert all(len(v) > 0 for v in result.values())
    
    def test_explain_all_function_features(self):
        """Test explain() for all function feature topics."""
        function_features = ['function', 'return', 'lambda', '*args', '**kwargs']
        
        for ff in function_features:
            result = explain(ff)
            
            assert isinstance(result, dict)
            assert set(result.keys()) == {'description', 'when_to_use', 'example'}
            assert all(len(v) > 0 for v in result.values())
    
    def test_explain_all_error_handling(self):
        """Test explain() for all error handling topics."""
        error_handling = ['try', 'except', 'finally', 'raise']
        
        for eh in error_handling:
            result = explain(eh)
            
            assert isinstance(result, dict)
            assert set(result.keys()) == {'description', 'when_to_use', 'example'}
            assert all(len(v) > 0 for v in result.values())
    
    def test_explain_all_file_operations(self):
        """Test explain() for all file operation topics."""
        file_operations = ['open', 'read', 'write', 'with']
        
        for fo in file_operations:
            result = explain(fo)
            
            assert isinstance(result, dict)
            assert set(result.keys()) == {'description', 'when_to_use', 'example'}
            assert all(len(v) > 0 for v in result.values())
    
    def test_explain_consistency(self):
        """Test that explain() returns consistent results."""
        result1 = explain("list")
        result2 = explain("list")
        result3 = explain("list")
        
        assert result1 == result2
        assert result2 == result3
    
    def test_explain_description_meaningful(self):
        """Test that descriptions are meaningful."""
        result = explain("list")
        description = result['description']
        
        # Should be substantial
        assert len(description) >= 20
        
        # Should contain alphabetic characters
        assert any(c.isalpha() for c in description)
    
    def test_explain_when_to_use_meaningful(self):
        """Test that when_to_use is meaningful."""
        result = explain("dict")
        when_to_use = result['when_to_use']
        
        # Should be substantial
        assert len(when_to_use) >= 20
        
        # Should contain alphabetic characters
        assert any(c.isalpha() for c in when_to_use)
    
    def test_explain_example_is_code(self):
        """Test that examples contain code."""
        result = explain("for")
        example = result['example']
        
        # Should contain code-like patterns
        code_indicators = ['=', '(', ')', '[', ']', '{', '}', 'print', 'def', 'if', 'for']
        assert any(indicator in example for indicator in code_indicators)
