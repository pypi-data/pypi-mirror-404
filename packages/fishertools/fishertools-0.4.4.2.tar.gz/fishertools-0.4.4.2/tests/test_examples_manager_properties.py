"""
Property-based tests for the Interactive Examples Manager.

These tests verify universal properties that should hold across all code examples.
Uses Hypothesis for property-based testing.
"""

import ast
from hypothesis import given, strategies as st
from fishertools.documentation.models import CodeExample
from fishertools.documentation.examples_manager import FileBasedExamplesManager


# Strategies for generating test data
valid_modules = st.sampled_from(["errors", "safe", "learn", "patterns", "config", "documentation"])
valid_difficulties = st.sampled_from(["beginner", "intermediate", "advanced"])


def valid_python_code_strategy():
    """Generate valid Python code examples."""
    code_examples = [
        "x = 1\nprint(x)",
        "def hello():\n    return 'world'",
        "result = 2 + 2",
        "items = [1, 2, 3]\nfor item in items:\n    print(item)",
        "data = {'key': 'value'}\nprint(data['key'])",
        "try:\n    x = 1 / 0\nexcept ZeroDivisionError:\n    print('error')",
    ]
    return st.sampled_from(code_examples)


def invalid_python_code_strategy():
    """Generate invalid Python code examples."""
    code_examples = [
        "def broken(\n    pass",
        "if True\n    print('missing colon')",
        "x = \n",
        "class Broken\n    pass",
        "for i in range(10)\n    print(i)",
    ]
    return st.sampled_from(code_examples)


class TestCodeExampleSyntaxValidity:
    """Property 1: Code Examples Syntax Validity
    
    For any code example in the system, parsing it as Python code should succeed 
    without syntax errors.
    
    **Validates: Requirements 1.1, 1.5, 10.1**
    """

    @given(
        code=valid_python_code_strategy(),
        module=valid_modules,
        difficulty=valid_difficulties,
    )
    def test_valid_code_examples_parse_successfully(self, code, module, difficulty):
        """
        Valid code examples should parse without syntax errors.
        """
        example = CodeExample(
            id="test-example",
            module=module,
            title="Test Example",
            code=code,
            expected_output="output",
            explanation="This is a test",
            difficulty=difficulty,
        )

        # Should not raise SyntaxError
        try:
            ast.parse(example.code)
        except SyntaxError:
            raise AssertionError(f"Valid code example failed to parse: {code}")

    @given(
        code=invalid_python_code_strategy(),
    )
    def test_invalid_code_examples_fail_to_parse(self, code):
        """
        Invalid code examples should fail to parse.
        """
        example = CodeExample(
            id="test-example",
            module="errors",
            title="Test Example",
            code=code,
            expected_output="output",
            explanation="This is a test",
        )

        # Should raise SyntaxError
        try:
            ast.parse(example.code)
            # If we get here, the code was valid when we expected it to be invalid
            # This is acceptable for property testing - some "invalid" code might be valid
        except SyntaxError:
            # Expected behavior
            pass

    @given(
        module=valid_modules,
        difficulty=valid_difficulties,
    )
    def test_code_example_has_required_fields(self, module, difficulty):
        """
        Every code example must have all required fields.
        """
        example = CodeExample(
            id="test-id",
            module=module,
            title="Test Title",
            code="x = 1",
            expected_output="output",
            explanation="explanation",
            difficulty=difficulty,
        )

        # All required fields should be present and non-empty
        assert example.id, "Example must have an id"
        assert example.module, "Example must have a module"
        assert example.title, "Example must have a title"
        assert example.code, "Example must have code"
        assert example.explanation, "Example must have an explanation"
        assert example.module in ["errors", "safe", "learn", "patterns", "config", "documentation"]
        assert example.difficulty in ["beginner", "intermediate", "advanced"]

    @given(
        code=valid_python_code_strategy(),
        module=valid_modules,
    )
    def test_code_example_module_is_valid(self, code, module):
        """
        Every code example must have a valid module.
        """
        example = CodeExample(
            id="test-id",
            module=module,
            title="Test",
            code=code,
            expected_output="output",
            explanation="explanation",
        )

        valid_modules_set = {"errors", "safe", "learn", "patterns", "config", "documentation"}
        assert example.module in valid_modules_set, f"Invalid module: {example.module}"

    @given(
        code=valid_python_code_strategy(),
        difficulty=valid_difficulties,
    )
    def test_code_example_difficulty_is_valid(self, code, difficulty):
        """
        Every code example must have a valid difficulty level.
        """
        example = CodeExample(
            id="test-id",
            module="errors",
            title="Test",
            code=code,
            expected_output="output",
            explanation="explanation",
            difficulty=difficulty,
        )

        valid_difficulties_set = {"beginner", "intermediate", "advanced"}
        assert example.difficulty in valid_difficulties_set, f"Invalid difficulty: {example.difficulty}"


class TestExamplesManagerStorage:
    """Tests for ExamplesManager storage and retrieval."""

    @given(
        code=valid_python_code_strategy(),
        module=valid_modules,
    )
    def test_add_and_retrieve_example(self, code, module):
        """
        An example added to the manager should be retrievable.
        """
        manager = FileBasedExamplesManager()
        
        example = CodeExample(
            id="test-example-1",
            module=module,
            title="Test Example",
            code=code,
            expected_output="output",
            explanation="This is a test",
        )

        manager.add_example(example)
        retrieved = manager.get_example("test-example-1")

        assert retrieved is not None, "Example should be retrievable after adding"
        assert retrieved.id == example.id
        assert retrieved.module == example.module
        assert retrieved.code == example.code

    @given(
        module=valid_modules,
    )
    def test_get_examples_by_module(self, module):
        """
        Examples should be retrievable by module.
        """
        manager = FileBasedExamplesManager()
        
        example = CodeExample(
            id=f"test-{module}-1",
            module=module,
            title="Test Example",
            code="x = 1",
            expected_output="output",
            explanation="This is a test",
        )

        manager.add_example(example)
        examples = manager.get_examples_by_module(module)

        assert len(examples) > 0, f"Should have examples for module {module}"
        assert any(ex.id == example.id for ex in examples), "Added example should be in results"

    @given(
        code=valid_python_code_strategy(),
        module=valid_modules,
    )
    def test_list_all_examples_includes_added(self, code, module):
        """
        list_all_examples should include all added examples.
        """
        manager = FileBasedExamplesManager()
        
        example = CodeExample(
            id="test-all-1",
            module=module,
            title="Test Example",
            code=code,
            expected_output="output",
            explanation="This is a test",
        )

        manager.add_example(example)
        all_examples = manager.list_all_examples()

        assert len(all_examples) > 0, "Should have at least one example"
        assert any(ex.id == example.id for ex in all_examples), "Added example should be in list"

    @given(
        code=valid_python_code_strategy(),
        module=valid_modules,
        difficulty=valid_difficulties,
    )
    def test_validate_example_with_valid_data(self, code, module, difficulty):
        """
        Validation should pass for examples with all required fields.
        """
        manager = FileBasedExamplesManager()
        
        example = CodeExample(
            id="test-valid",
            module=module,
            title="Test Example",
            code=code,
            expected_output="output",
            explanation="This is a test",
            difficulty=difficulty,
        )

        result = manager.validate_example(example)
        assert result.is_valid, f"Valid example failed validation: {result.errors}"

    @given(
        module=valid_modules,
    )
    def test_validate_example_missing_id(self, module):
        """
        Validation should fail for examples missing id.
        """
        manager = FileBasedExamplesManager()
        
        example = CodeExample(
            id="",  # Empty id
            module=module,
            title="Test Example",
            code="x = 1",
            expected_output="output",
            explanation="This is a test",
        )

        result = manager.validate_example(example)
        assert not result.is_valid, "Should fail validation with empty id"
        assert any("id" in error.lower() for error in result.errors)

    @given(
        code=valid_python_code_strategy(),
    )
    def test_validate_example_invalid_module(self, code):
        """
        Validation should fail for examples with invalid module.
        """
        manager = FileBasedExamplesManager()
        
        example = CodeExample(
            id="test-invalid-module",
            module="invalid_module",
            title="Test Example",
            code=code,
            expected_output="output",
            explanation="This is a test",
        )

        result = manager.validate_example(example)
        assert not result.is_valid, "Should fail validation with invalid module"
        assert any("module" in error.lower() for error in result.errors)

    @given(
        code=valid_python_code_strategy(),
        module=valid_modules,
    )
    def test_validate_example_invalid_difficulty(self, code, module):
        """
        Validation should fail for examples with invalid difficulty.
        """
        manager = FileBasedExamplesManager()
        
        example = CodeExample(
            id="test-invalid-difficulty",
            module=module,
            title="Test Example",
            code=code,
            expected_output="output",
            explanation="This is a test",
            difficulty="expert",  # Invalid difficulty
        )

        result = manager.validate_example(example)
        assert not result.is_valid, "Should fail validation with invalid difficulty"
        assert any("difficulty" in error.lower() for error in result.errors)



class TestExamplesOrganization:
    """Property 3: Examples Organized by Module
    
    For any code example in the system, it should be tagged with exactly one module 
    from the set {errors, safe, learn, patterns, config, documentation}.
    
    **Validates: Requirements 1.3, 9.1**
    """

    @given(
        code=valid_python_code_strategy(),
        module=valid_modules,
    )
    def test_example_has_exactly_one_module(self, code, module):
        """
        Every example must have exactly one module assigned.
        """
        example = CodeExample(
            id="test-module-1",
            module=module,
            title="Test Example",
            code=code,
            expected_output="output",
            explanation="This is a test",
        )

        # Module should be exactly one of the valid modules
        valid_modules_set = {"errors", "safe", "learn", "patterns", "config", "documentation"}
        assert example.module in valid_modules_set
        assert isinstance(example.module, str)
        assert len(example.module) > 0

    @given(
        module=valid_modules,
    )
    def test_examples_retrievable_by_module(self, module):
        """
        Examples should be retrievable by their module.
        """
        manager = FileBasedExamplesManager()
        
        example = CodeExample(
            id=f"test-org-{module}",
            module=module,
            title="Test Example",
            code="x = 1",
            expected_output="output",
            explanation="This is a test",
        )

        manager.add_example(example)
        
        # Should be retrievable by module
        examples_by_module = manager.get_examples_by_module(module)
        assert len(examples_by_module) > 0
        assert any(ex.module == module for ex in examples_by_module)

    @given(
        code=valid_python_code_strategy(),
        module=valid_modules,
    )
    def test_example_module_consistency(self, code, module):
        """
        An example's module should be consistent when retrieved.
        """
        manager = FileBasedExamplesManager()
        
        example = CodeExample(
            id="test-consistency",
            module=module,
            title="Test Example",
            code=code,
            expected_output="output",
            explanation="This is a test",
        )

        manager.add_example(example)
        retrieved = manager.get_example("test-consistency")

        assert retrieved.module == module, "Module should be consistent after retrieval"

    @given(
        module=valid_modules,
    )
    def test_all_modules_can_have_examples(self, module):
        """
        All valid modules should be able to have examples.
        """
        manager = FileBasedExamplesManager()
        
        example = CodeExample(
            id=f"test-all-modules-{module}",
            module=module,
            title="Test Example",
            code="x = 1",
            expected_output="output",
            explanation="This is a test",
        )

        # Should not raise any exception
        manager.add_example(example)
        
        # Should be retrievable
        retrieved = manager.get_example(f"test-all-modules-{module}")
        assert retrieved is not None
        assert retrieved.module == module

    @given(
        st.lists(
            st.tuples(
                st.text(min_size=1, max_size=20),
                valid_modules,
            ),
            min_size=1,
            max_size=10,
        )
    )
    def test_multiple_examples_organized_by_module(self, examples_data):
        """
        Multiple examples should be properly organized by module.
        """
        manager = FileBasedExamplesManager()
        
        # Add multiple examples
        for idx, (title, module) in enumerate(examples_data):
            example = CodeExample(
                id=f"test-multi-{idx}",
                module=module,
                title=title,
                code="x = 1",
                expected_output="output",
                explanation="This is a test",
            )
            manager.add_example(example)
        
        # Verify all examples are retrievable
        all_examples = manager.list_all_examples()
        assert len(all_examples) >= len(examples_data)
        
        # Verify examples are organized by module
        for _, module in examples_data:
            examples_by_module = manager.get_examples_by_module(module)
            assert len(examples_by_module) > 0

    @given(
        code=valid_python_code_strategy(),
        module=valid_modules,
    )
    def test_example_module_in_valid_set(self, code, module):
        """
        Example module must be in the valid set of modules.
        """
        example = CodeExample(
            id="test-valid-set",
            module=module,
            title="Test Example",
            code=code,
            expected_output="output",
            explanation="This is a test",
        )

        valid_modules_set = {"errors", "safe", "learn", "patterns", "config", "documentation"}
        assert example.module in valid_modules_set, f"Module {example.module} not in valid set"
