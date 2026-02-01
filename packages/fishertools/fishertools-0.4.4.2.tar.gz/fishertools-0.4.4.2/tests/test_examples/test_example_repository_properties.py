"""
Property-based tests for Example Repository quality.

Feature: fishertools-enhancements, Property 3: Example Repository Quality
Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5
"""

import pytest
from hypothesis import given, strategies as st, assume
from fishertools.examples import ExampleRepository
from fishertools.examples.models import (
    CodeExample, ExampleCategory, ProjectType, Scenario
)


class TestExampleRepositoryQuality:
    """Property tests for Example Repository quality and completeness."""
    
    def test_repository_initialization(self):
        """Test that repository initializes with default examples."""
        # Feature: fishertools-enhancements, Property 3: Example Repository Quality
        repo = ExampleRepository()
        
        # Should have examples for beginners
        list_examples = repo.get_examples_by_topic("lists")
        dict_examples = repo.get_examples_by_topic("dictionaries")
        input_examples = repo.get_examples_by_category(ExampleCategory.USER_INPUT)
        
        assert len(list_examples) > 0, "Should have list examples for beginners"
        assert len(dict_examples) > 0, "Should have dictionary examples for beginners"
        assert len(input_examples) > 0, "Should have user input examples for beginners"
    
    @given(st.sampled_from(list(ExampleCategory)))
    def test_category_examples_have_required_properties(self, category):
        """Test that all examples in a category have required properties."""
        # Feature: fishertools-enhancements, Property 3: Example Repository Quality
        repo = ExampleRepository()
        examples = repo.get_examples_by_category(category)
        
        for example in examples:
            # All examples should have basic required properties
            assert example.id, "Example should have an ID"
            assert example.title, "Example should have a title"
            assert example.description, "Example should have a description"
            assert example.code, "Example should have code"
            assert example.explanation, "Example should have an explanation"
            assert example.difficulty in ["beginner", "intermediate", "advanced"], \
                "Example should have valid difficulty level"
            assert example.topics, "Example should have topics"
            assert example.category == category, "Example should match requested category"
    
    @given(st.text(min_size=1, max_size=20).filter(lambda x: x.strip()))
    def test_search_functionality_completeness(self, query):
        """Test that search finds relevant examples."""
        # Feature: fishertools-enhancements, Property 3: Example Repository Quality
        repo = ExampleRepository()
        
        # Add a test example that should match the query
        test_example = CodeExample(
            id=f"test_{query.lower().replace(' ', '_')}",
            title=f"Example about {query}",
            description=f"This example demonstrates {query}",
            code=f"# Code for {query}\nprint('{query}')",
            explanation=f"This explains {query}",
            difficulty="beginner",
            topics=[query.lower()],
            prerequisites=[],
            category=ExampleCategory.BASIC_SYNTAX
        )
        repo.add_example(test_example)
        
        # Search should find the example
        results = repo.search_examples(query)
        found_ids = [ex.id for ex in results]
        
        assert test_example.id in found_ids, \
            f"Search for '{query}' should find the matching example"
    
    def test_beginner_scenarios_completeness(self):
        """Test that beginner scenarios provide comprehensive learning paths."""
        # Feature: fishertools-enhancements, Property 3: Example Repository Quality
        repo = ExampleRepository()
        scenarios = repo.get_beginner_scenarios()
        
        assert len(scenarios) > 0, "Should have beginner scenarios"
        
        for scenario in scenarios:
            assert scenario.difficulty == "beginner", "All scenarios should be beginner level"
            assert scenario.examples, "Scenario should contain examples"
            assert scenario.learning_objectives, "Scenario should have learning objectives"
            assert scenario.estimated_time > 0, "Scenario should have estimated time"
            
            # All examples in scenario should be beginner-friendly
            for example in scenario.examples:
                assert example.difficulty == "beginner", \
                    "All examples in beginner scenario should be beginner level"
    
    @given(st.sampled_from(list(ProjectType)))
    def test_project_templates_have_step_by_step_instructions(self, project_type):
        """Test that project templates provide step-by-step instructions."""
        # Feature: fishertools-enhancements, Property 3: Example Repository Quality
        repo = ExampleRepository()
        project = repo.create_simple_project(project_type)
        
        assert project.project_type == project_type, "Project should match requested type"
        assert project.difficulty == "beginner", "Simple projects should be beginner level"
        assert project.steps, "Project should have steps"
        assert project.final_code, "Project should have final code"
        assert project.estimated_time > 0, "Project should have estimated time"
        
        # Each step should have proper structure
        for i, step in enumerate(project.steps):
            assert step.step_number == i + 1, "Steps should be numbered sequentially"
            assert step.title, "Step should have a title"
            assert step.description, "Step should have a description"
    
    def test_line_by_line_explanations_completeness(self):
        """Test that line-by-line explanations cover all code lines."""
        # Feature: fishertools-enhancements, Property 3: Example Repository Quality
        repo = ExampleRepository()
        
        # Get a sample example
        examples = repo.get_examples_by_category(ExampleCategory.COLLECTIONS)
        assume(len(examples) > 0)
        
        example = examples[0]
        explanation = repo.explain_example_line_by_line(example)
        
        # Count non-empty lines in original code
        code_lines = [line for line in example.code.strip().split('\n')]
        explanation_lines = explanation.lines
        
        assert len(explanation_lines) == len(code_lines), \
            "Should have explanation for every line of code"
        
        assert explanation.example_id == example.id, \
            "Explanation should reference correct example"
        assert explanation.summary, "Explanation should have a summary"
        assert explanation.key_concepts, "Explanation should identify key concepts"
        
        # Each line explanation should have required properties
        for line_exp in explanation_lines:
            assert line_exp.line_number > 0, "Line number should be positive"
            assert line_exp.explanation, "Each line should have an explanation"
    
    def test_safe_user_input_examples_security(self):
        """Test that user input examples demonstrate safe practices."""
        # Feature: fishertools-enhancements, Property 3: Example Repository Quality
        repo = ExampleRepository()
        input_examples = repo.get_examples_by_category(ExampleCategory.USER_INPUT)
        
        assert len(input_examples) > 0, "Should have user input examples"
        
        for example in input_examples:
            code = example.code.lower()
            
            # Should demonstrate input validation
            assert 'try:' in code or 'except' in code or 'if' in code, \
                "User input examples should show validation or error handling"
            
            # Should use safe input practices
            if 'input(' in code:
                assert '.strip()' in code or 'strip(' in code, \
                    "Should demonstrate input cleaning with strip()"
    
    def test_collection_examples_cover_basic_operations(self):
        """Test that collection examples cover fundamental operations."""
        # Feature: fishertools-enhancements, Property 3: Example Repository Quality
        repo = ExampleRepository()
        
        # Test list examples
        list_examples = repo.get_examples_by_topic("lists")
        assert len(list_examples) > 0, "Should have list examples"
        
        list_code = " ".join([ex.code.lower() for ex in list_examples])
        assert 'append(' in list_code, "List examples should show append operation"
        assert '[' in list_code and ']' in list_code, "List examples should show list creation"
        
        # Test dictionary examples  
        dict_examples = repo.get_examples_by_topic("dictionaries")
        assert len(dict_examples) > 0, "Should have dictionary examples"
        
        dict_code = " ".join([ex.code.lower() for ex in dict_examples])
        assert '{' in dict_code and '}' in dict_code, "Dict examples should show dict creation"
        assert '.get(' in dict_code or 'get(' in dict_code, \
            "Dict examples should show safe access with get()"
    
    @given(st.text(min_size=1, max_size=50).filter(lambda x: x.strip()))
    def test_concept_breakdown_provides_simple_steps(self, concept):
        """Test that complex concepts are broken down into simple steps."""
        # Feature: fishertools-enhancements, Property 3: Example Repository Quality
        repo = ExampleRepository()
        
        steps = repo.break_down_complex_concept(concept)
        
        assert len(steps) > 0, "Should provide breakdown steps for any concept"
        assert all(isinstance(step, str) for step in steps), \
            "All breakdown steps should be strings"
        assert all(len(step.strip()) > 0 for step in steps), \
            "All breakdown steps should have content"
        
        # Steps should mention the concept
        concept_mentioned = any(concept.lower() in step.lower() for step in steps)
        assert concept_mentioned, f"Breakdown should mention the concept '{concept}'"