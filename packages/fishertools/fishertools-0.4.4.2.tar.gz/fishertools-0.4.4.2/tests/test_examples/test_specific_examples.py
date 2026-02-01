"""
Unit tests for specific examples in the Example Repository.

Tests security of user input examples, correctness of collection examples,
and completeness of step-by-step instructions.
Requirements: 3.2, 3.3
"""

import pytest
from fishertools.examples import ExampleRepository
from fishertools.examples.models import ExampleCategory, ProjectType


class TestSpecificExamples:
    """Unit tests for specific example scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.repo = ExampleRepository()
    
    def test_user_input_examples_security(self):
        """Test that user input examples demonstrate secure practices."""
        input_examples = self.repo.get_examples_by_category(ExampleCategory.USER_INPUT)
        
        # Should have at least one user input example
        assert len(input_examples) > 0
        
        # Check the safe input basics example specifically
        safe_input_example = None
        for example in input_examples:
            if "safe_input_basics" in example.id:
                safe_input_example = example
                break
        
        assert safe_input_example is not None, "Should have safe input basics example"
        
        # Verify security practices in the code
        code = safe_input_example.code
        
        # Should use strip() to clean input
        assert ".strip()" in code, "Should demonstrate input cleaning with strip()"
        
        # Should use try-except for type conversion
        assert "try:" in code and "except ValueError:" in code, \
            "Should demonstrate error handling for type conversion"
        
        # Should validate input ranges
        assert "< 0" in code or "> 0" in code, \
            "Should demonstrate input validation"
        
        # Should use loops for input validation
        assert "while True:" in code, \
            "Should demonstrate input validation loops"
        
        # Should provide user feedback for invalid input
        assert "Please" in code and ("try again" in code or "enter" in code), \
            "Should provide helpful error messages"
    
    def test_list_examples_correctness(self):
        """Test that list examples demonstrate correct operations."""
        list_examples = self.repo.get_examples_by_topic("lists")
        
        assert len(list_examples) >= 2, "Should have multiple list examples"
        
        # Check basic list example
        basic_example = None
        operations_example = None
        
        for example in list_examples:
            if "list_basics" in example.id:
                basic_example = example
            elif "list_operations" in example.id:
                operations_example = example
        
        assert basic_example is not None, "Should have basic list example"
        assert operations_example is not None, "Should have list operations example"
        
        # Test basic list operations
        basic_code = basic_example.code
        assert "fruits = [" in basic_code, "Should show list creation"
        assert ".append(" in basic_code, "Should show append operation"
        assert ".extend(" in basic_code, "Should show extend operation"
        assert "[0]" in basic_code, "Should show indexing"
        assert "[-1]" in basic_code, "Should show negative indexing"
        
        # Test advanced list operations
        ops_code = operations_example.code
        assert ".sort()" in ops_code, "Should show in-place sorting"
        assert "sorted(" in ops_code, "Should show non-destructive sorting"
        assert ".index(" in ops_code, "Should show searching"
        assert ".remove(" in ops_code, "Should show item removal"
        assert ".pop()" in ops_code, "Should show pop operation"
        assert "[x**2 for x in" in ops_code, "Should show list comprehension"
    
    def test_dictionary_examples_correctness(self):
        """Test that dictionary examples demonstrate correct operations."""
        dict_examples = self.repo.get_examples_by_topic("dictionaries")
        
        assert len(dict_examples) >= 1, "Should have dictionary examples"
        
        # Check basic dictionary example
        basic_example = None
        for example in dict_examples:
            if "dict_basics" in example.id:
                basic_example = example
                break
        
        assert basic_example is not None, "Should have basic dictionary example"
        
        code = basic_example.code
        
        # Should demonstrate dictionary creation
        assert "student = {" in code, "Should show dictionary creation"
        
        # Should show both direct access and safe access
        assert "student['" in code, "Should show direct key access"
        assert ".get(" in code, "Should show safe access with get()"
        
        # Should demonstrate key existence checking
        assert "in student" in code, "Should show key existence checking"
        
        # Should show dictionary methods
        assert ".keys()" in code, "Should show keys() method"
        assert ".values()" in code, "Should show values() method"
        
        # Should demonstrate adding new key-value pairs
        assert "student['" in code and "=" in code, "Should show adding new keys"
    
    def test_project_step_by_step_completeness(self):
        """Test that project templates have complete step-by-step instructions."""
        calculator_project = self.repo.create_simple_project(ProjectType.CALCULATOR)
        
        # Should have proper project structure
        assert calculator_project.title, "Project should have a title"
        assert calculator_project.description, "Project should have a description"
        assert calculator_project.difficulty == "beginner", "Should be beginner level"
        assert calculator_project.estimated_time > 0, "Should have estimated time"
        
        # Should have multiple steps
        assert len(calculator_project.steps) >= 2, "Should have multiple steps"
        
        # Check first step (function definitions)
        first_step = calculator_project.steps[0]
        assert first_step.step_number == 1, "First step should be numbered 1"
        assert "function" in first_step.title.lower(), "First step should be about functions"
        assert first_step.code_snippet, "Step should have code snippet"
        assert first_step.explanation, "Step should have explanation"
        assert first_step.hints, "Step should have hints"
        
        # Code should include basic arithmetic functions
        code = first_step.code_snippet
        assert "def add(" in code, "Should define add function"
        assert "def subtract(" in code, "Should define subtract function"
        assert "def multiply(" in code, "Should define multiply function"
        assert "def divide(" in code, "Should define divide function"
        assert "if b == 0:" in code, "Should handle division by zero"
        
        # Check second step (main loop)
        second_step = calculator_project.steps[1]
        assert second_step.step_number == 2, "Second step should be numbered 2"
        assert "loop" in second_step.title.lower() or "main" in second_step.title.lower(), \
            "Second step should be about main loop"
        
        main_code = second_step.code_snippet
        assert "while True:" in main_code, "Should have main loop"
        assert "input(" in main_code, "Should get user input"
        assert "try:" in main_code and "except" in main_code, \
            "Should handle input errors"
        assert "quit" in main_code.lower(), "Should allow user to quit"
        
        # Final code should be complete and runnable
        final_code = calculator_project.final_code
        assert "def add(" in final_code, "Final code should include all functions"
        assert "def calculator(" in final_code, "Final code should include main function"
        assert "if __name__" in final_code, "Final code should have main guard"
        
        # Should have extension suggestions
        assert calculator_project.extensions, "Should suggest extensions"
        assert len(calculator_project.extensions) > 0, "Should have extension ideas"
    
    def test_line_by_line_explanation_accuracy(self):
        """Test that line-by-line explanations are accurate and helpful."""
        # Get a specific example to test
        list_examples = self.repo.get_examples_by_topic("lists")
        basic_example = None
        
        for example in list_examples:
            if "list_basics" in example.id:
                basic_example = example
                break
        
        assert basic_example is not None, "Should have basic list example"
        
        # Generate line-by-line explanation
        explanation = self.repo.explain_example_line_by_line(basic_example)
        
        # Should have explanation for each line
        code_lines = basic_example.code.strip().split('\n')
        assert len(explanation.lines) == len(code_lines), \
            "Should have explanation for each line"
        
        # Check specific line explanations
        explanations_text = [line.explanation.lower() for line in explanation.lines]
        
        # Should identify list creation
        list_creation_found = any("list" in exp and ("create" in exp or "assign" in exp) 
                                 for exp in explanations_text)
        assert list_creation_found, "Should identify list creation"
        
        # Should identify indexing
        indexing_found = any("index" in exp or "access" in exp 
                           for exp in explanations_text)
        assert indexing_found, "Should identify indexing operations"
        
        # Should identify method calls
        method_found = any(("append" in exp or "extend" in exp or 
                           ("adds" in exp and ("item" in exp or "multiple" in exp)))
                          for exp in explanations_text)
        assert method_found, "Should identify method calls"
        
        # Summary should be comprehensive
        summary = explanation.summary.lower()
        assert "list" in summary, "Summary should mention lists"
        assert len(explanation.key_concepts) > 0, "Should identify key concepts"
        assert "lists" in explanation.key_concepts, "Should identify lists as key concept"
    
    def test_concept_breakdown_accuracy(self):
        """Test that concept breakdowns are accurate and educational."""
        # Test specific concept breakdowns
        list_comp_breakdown = self.repo.break_down_complex_concept("list comprehension")
        
        assert len(list_comp_breakdown) >= 3, "Should have multiple breakdown steps"
        
        breakdown_text = " ".join(list_comp_breakdown).lower()
        assert "list comprehension" in breakdown_text, "Should mention the concept"
        assert "expression" in breakdown_text, "Should explain expression part"
        assert "iterable" in breakdown_text, "Should explain iterable part"
        assert "for" in breakdown_text, "Should mention for loop connection"
        
        # Test exception handling breakdown
        exception_breakdown = self.repo.break_down_complex_concept("exception handling")
        
        exception_text = " ".join(exception_breakdown).lower()
        assert "exception" in exception_text or "error" in exception_text, \
            "Should mention exceptions or errors"
        assert "try" in exception_text, "Should mention try blocks"
        assert "except" in exception_text, "Should mention except blocks"
        
        # Test prerequisites
        list_comp_prereqs = self.repo.get_concept_prerequisites("list comprehension")
        assert "lists" in list_comp_prereqs, "List comprehension should require lists knowledge"
        assert "for loops" in list_comp_prereqs, "List comprehension should require loop knowledge"
    
    def test_search_functionality_specific_cases(self):
        """Test search functionality with specific queries."""
        # Search for lists
        list_results = self.repo.search_examples("list")
        assert len(list_results) > 0, "Should find list examples"
        
        # All results should be relevant to lists
        for result in list_results:
            result_text = (result.title + " " + result.description + " " + 
                          " ".join(result.topics) + " " + result.code).lower()
            assert "list" in result_text, "Search results should be relevant"
        
        # Search for dictionaries
        dict_results = self.repo.search_examples("dictionary")
        assert len(dict_results) > 0, "Should find dictionary examples"
        
        # Search with category filter
        input_results = self.repo.search_examples("input", ExampleCategory.USER_INPUT)
        assert len(input_results) > 0, "Should find input examples in USER_INPUT category"
        
        for result in input_results:
            assert result.category == ExampleCategory.USER_INPUT, \
                "Filtered results should match category"
    
    def test_example_safety_and_best_practices(self):
        """Test that examples follow safety and best practices."""
        all_examples = []
        for category in ExampleCategory:
            all_examples.extend(self.repo.get_examples_by_category(category))
        
        assert len(all_examples) > 0, "Should have examples to test"
        
        for example in all_examples:
            code = example.code
            
            # Should not use dangerous practices
            assert "eval(" not in code, "Examples should not use eval()"
            assert "exec(" not in code, "Examples should not use exec()"
            
            # Input examples should be safe
            if example.category == ExampleCategory.USER_INPUT:
                if "input(" in code:
                    # Should validate or clean input
                    assert (".strip()" in code or "try:" in code or 
                           "if " in code), "Input examples should validate input"
            
            # Should have proper error handling where needed for user input
            if ("int(" in code or "float(" in code) and "input(" in code:
                assert ("try:" in code and "except" in code), \
                    "Type conversion of user input should have error handling"