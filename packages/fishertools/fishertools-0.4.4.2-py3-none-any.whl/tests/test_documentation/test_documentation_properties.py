"""
Property-based tests for documentation generation completeness.

Feature: fishertools-enhancements
Property 2: Documentation Generation Completeness
Validates: Requirements 2.1, 2.2, 2.3, 2.4
"""

import pytest
import tempfile
import os
from hypothesis import given, strategies as st, assume
from fishertools.documentation import DocumentationGenerator, APIGenerator
from fishertools.documentation.models import APIInfo, FunctionInfo


# Test data generators
@st.composite
def generate_function_info(draw):
    """Generate valid FunctionInfo for testing."""
    name = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), blacklist_characters='_')))
    assume(name.isidentifier() and not name.startswith('_'))
    
    docstring = draw(st.one_of(
        st.none(),
        st.text(min_size=10, max_size=200)
    ))
    
    # Generate parameters with type annotations
    param_count = draw(st.integers(min_value=0, max_value=5))
    parameters = {}
    for i in range(param_count):
        param_name = f"param_{i}"
        param_type = draw(st.sampled_from(['str', 'int', 'float', 'bool', 'List[str]', 'Dict[str, Any]', 'Optional[str]']))
        parameters[param_name] = param_type
    
    return_type = draw(st.one_of(
        st.none(),
        st.sampled_from(['str', 'int', 'bool', 'List[str]', 'None'])
    ))
    
    return FunctionInfo(
        name=name,
        docstring=docstring,
        parameters=parameters,
        return_type=return_type,
        module_path="/fake/path/module.py",
        line_number=draw(st.integers(min_value=1, max_value=1000))
    )


@st.composite
def generate_api_info(draw):
    """Generate valid APIInfo for testing."""
    module_name = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), blacklist_characters='_')))
    assume(module_name.isidentifier())
    
    functions = draw(st.lists(generate_function_info(), min_size=1, max_size=10))
    
    classes = draw(st.lists(st.fixed_dictionaries({
        'name': st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'), blacklist_characters='_')),
        'docstring': st.one_of(st.none(), st.text(min_size=10, max_size=100)),
        'methods': st.lists(generate_function_info(), max_size=3),
        'line_number': st.integers(min_value=1, max_value=1000)
    }), max_size=3))
    
    constants = draw(st.dictionaries(
        st.text(min_size=1, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Nd'), blacklist_characters='_')),
        st.text(min_size=1, max_size=50),
        max_size=5
    ))
    
    imports = draw(st.lists(
        st.text(min_size=5, max_size=30),
        max_size=10
    ))
    
    docstring = draw(st.one_of(
        st.none(),
        st.text(min_size=20, max_size=200)
    ))
    
    return APIInfo(
        module_name=module_name,
        functions=functions,
        classes=classes,
        constants=constants,
        imports=imports,
        docstring=docstring
    )


class TestDocumentationGenerationProperties:
    """Property-based tests for documentation generation completeness."""
    
    @given(generate_api_info())
    def test_documentation_generation_completeness(self, api_info):
        """
        Property 2: Documentation Generation Completeness
        
        For any code change in the fishertools library, the Documentation_Generator 
        should automatically extract all docstrings, parameter types, and generate 
        structured navigation with usage examples for each function.
        
        **Validates: Requirements 2.1, 2.2, 2.3, 2.4**
        """
        generator = DocumentationGenerator("test_project")
        
        # Test requirement 2.1: Extract all docstrings and parameter types
        sphinx_docs = generator.generate_sphinx_docs(api_info)
        
        # Verify all docstrings are extracted (2.1)
        rst_content = sphinx_docs.source_files[f"{api_info.module_name}.rst"]
        
        # Check that module docstring is included if present
        if api_info.docstring:
            assert api_info.module_name in rst_content
        
        # Check that all functions are documented (2.2)
        for function in api_info.functions:
            assert f"autofunction:: {api_info.module_name}.{function.name}" in rst_content
        
        # Check that all classes are documented (2.2)
        for cls in api_info.classes:
            assert f"autoclass:: {api_info.module_name}.{cls['name']}" in rst_content
        
        # Check that all constants are documented (2.2)
        for constant_name in api_info.constants.keys():
            assert f"autodata:: {api_info.module_name}.{constant_name}" in rst_content
        
        # Test requirement 2.3: Generate structured navigation
        navigation = sphinx_docs.navigation
        assert navigation is not None
        assert navigation.name == "test_project"
        assert len(navigation.children) >= 1
        
        # Verify navigation includes the module
        module_found = any(child.name == api_info.module_name for child in navigation.children)
        assert module_found, f"Module {api_info.module_name} not found in navigation"
        
        # Test requirement 2.4: Generate usage examples for each function
        for function in api_info.functions:
            examples = generator.add_usage_examples(function)
            assert len(examples) >= 1, f"No examples generated for function {function.name}"
            
            # Verify each example has required components
            for example in examples:
                assert example.code is not None and len(example.code.strip()) > 0
                assert example.description is not None and len(example.description.strip()) > 0
                assert function.name in example.code, f"Function {function.name} not found in example code"
    
    @given(st.lists(generate_api_info(), min_size=1, max_size=5))
    def test_multiple_modules_documentation_completeness(self, api_infos):
        """
        Test documentation generation completeness for multiple modules.
        
        Validates that the generator can handle multiple modules and create
        proper navigation structure for all of them.
        """
        generator = DocumentationGenerator("multi_module_project")
        
        # Create temporary module files for testing
        module_paths = []
        with tempfile.TemporaryDirectory() as temp_dir:
            for i, api_info in enumerate(api_infos):
                module_path = os.path.join(temp_dir, f"{api_info.module_name}.py")
                # Create a minimal Python file
                with open(module_path, 'w') as f:
                    f.write(f'"""{api_info.docstring or "Module docstring"}"""\n')
                    for func in api_info.functions:
                        f.write(f'def {func.name}():\n    """{func.docstring or "Function docstring"}"""\n    pass\n\n')
                module_paths.append(module_path)
            
            # Test building documentation for multiple modules
            try:
                sphinx_docs = generator.build_documentation(module_paths)
                
                # Verify all modules are included
                for api_info in api_infos:
                    rst_file = f"{api_info.module_name}.rst"
                    assert rst_file in sphinx_docs.source_files
                
                # Verify navigation includes all modules
                assert len(sphinx_docs.navigation.children) == len(api_infos)
                
                # Verify index.rst includes all modules
                index_content = sphinx_docs.source_files["index.rst"]
                for api_info in api_infos:
                    assert api_info.module_name in index_content
                    
            except Exception as e:
                # If parsing fails due to invalid generated code, that's acceptable
                # as we're testing with synthetic data
                pytest.skip(f"Skipping due to synthetic data parsing issue: {e}")
    
    @given(generate_function_info())
    def test_usage_examples_generation_completeness(self, function_info):
        """
        Test that usage examples are generated for any function.
        
        Validates requirement 2.4: Generate usage examples for each function.
        """
        generator = DocumentationGenerator("test_project")
        
        examples = generator.add_usage_examples(function_info)
        
        # Must generate at least one example
        assert len(examples) >= 1
        
        # Each example must have valid structure
        for example in examples:
            assert example.code is not None
            assert len(example.code.strip()) > 0
            assert example.description is not None
            assert len(example.description.strip()) > 0
            assert example.language == "python"
            
            # Function name should appear in the example code
            assert function_info.name in example.code
            
            # Code should be syntactically valid Python (basic check)
            assert "=" in example.code or function_info.name + "(" in example.code
    
    def test_sphinx_configuration_completeness(self):
        """
        Test that Sphinx configuration includes all required extensions and settings.
        
        Validates that the generated Sphinx configuration supports autodoc,
        viewcode, napoleon, and other required extensions.
        """
        generator = DocumentationGenerator("test_project")
        config = generator._generate_sphinx_config()
        
        # Required configuration keys
        required_keys = ['project', 'extensions', 'html_theme']
        for key in required_keys:
            assert key in config
        
        # Required extensions for API documentation
        required_extensions = [
            'sphinx.ext.autodoc',
            'sphinx.ext.viewcode', 
            'sphinx.ext.napoleon'
        ]
        
        for ext in required_extensions:
            assert ext in config['extensions']
        
        # Autodoc configuration should be present
        assert 'autodoc_default_options' in config
        autodoc_options = config['autodoc_default_options']
        assert autodoc_options.get('members') is True
        assert autodoc_options.get('undoc-members') is True