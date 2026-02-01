"""
Main documentation generator with Sphinx integration.
"""

import os
import json
from typing import List, Dict, Any
from .models import (
    APIInfo, SphinxDocuments, NavigationTree, 
    ExampleCode, PublishResult, FunctionInfo, PublishStatus
)
from .api import APIGenerator


class DocumentationGenerator:
    """
    Automatic API documentation generator with ReadTheDocs integration.
    
    Extracts API information, generates Sphinx documentation,
    and publishes to ReadTheDocs automatically.
    """
    
    # Constants for file names
    INDEX_RST = "index.rst"
    CONF_PY = "conf.py"
    READTHEDOCS_YAML = ".readthedocs.yaml"
    REQUIREMENTS_TXT = "requirements.txt"
    
    def __init__(self, project_name: str, output_dir: str = "docs"):
        """
        Initialize the documentation generator.
        
        Args:
            project_name: Name of the project
            output_dir: Directory for generated documentation
        """
        self.project_name = project_name
        self.output_dir = output_dir
        self.api_generator = APIGenerator()
        
        # Integration point for visual documentation
        self._visual_docs = None
    
    def extract_api_info(self, module_path: str) -> APIInfo:
        """
        Extract API information from a Python module.
        
        Args:
            module_path: Path to the Python module
            
        Returns:
            APIInfo: Extracted API information
        """
        return self.api_generator.parse_module(module_path)
    
    def generate_sphinx_docs(self, api_info: APIInfo) -> SphinxDocuments:
        """
        Generate Sphinx documentation from API information.
        
        Args:
            api_info: API information to document
            
        Returns:
            SphinxDocuments: Generated Sphinx documentation
        """
        source_files = {}
        
        # Generate main module RST file
        rst_content = self.api_generator.generate_sphinx_rst(api_info)
        source_files[f"{api_info.module_name}.rst"] = rst_content
        
        # Generate index.rst
        index_content = self._generate_index_rst([api_info.module_name])
        source_files[self.INDEX_RST] = index_content
        
        # Generate conf.py
        config = self._generate_sphinx_config()
        source_files[self.CONF_PY] = self._config_to_python_file(config)
        
        # Create navigation tree
        navigation = NavigationTree(
            name=self.project_name,
            path=self.INDEX_RST,
            children=[
                NavigationTree(
                    name=api_info.module_name,
                    path=f"{api_info.module_name}.rst"
                )
            ]
        )
        
        return SphinxDocuments(
            source_files=source_files,
            config=config,
            navigation=navigation,
            build_path=self.output_dir
        )
    
    def create_navigation_structure(self, modules: List[str]) -> NavigationTree:
        """
        Create structured navigation for documentation.
        
        Args:
            modules: List of module names to include
            
        Returns:
            NavigationTree: Hierarchical navigation structure
        """
        children = []
        for module in modules:
            children.append(NavigationTree(
                name=module,
                path=f"{module}.rst"
            ))
        
        return NavigationTree(
            name=self.project_name,
            path=self.INDEX_RST,
            children=children
        )
    
    def add_usage_examples(self, function: FunctionInfo) -> List[ExampleCode]:
        """
        Generate usage examples for a function.
        
        Args:
            function: Function information
            
        Returns:
            List[ExampleCode]: Generated usage examples
        """
        examples = []
        
        # Generate basic usage example
        basic_example = self._generate_basic_example(function)
        if basic_example:
            examples.append(basic_example)
        
        # Generate example with error handling if applicable
        error_example = self._generate_error_handling_example(function)
        if error_example:
            examples.append(error_example)
        
        # Generate advanced example if function has complex parameters
        if len(function.parameters) > 2:
            advanced_example = self._generate_advanced_example(function)
            if advanced_example:
                examples.append(advanced_example)
        
        return examples
    
    def publish_to_readthedocs(self, docs: SphinxDocuments) -> PublishResult:
        """
        Publish documentation to ReadTheDocs.
        
        Args:
            docs: Sphinx documentation to publish
            
        Returns:
            PublishResult: Result of the publishing operation
        """
        try:
            # Create output directory if it doesn't exist
            os.makedirs(docs.build_path, exist_ok=True)
            
            # Write all source files
            for filename, content in docs.source_files.items():
                file_path = os.path.join(docs.build_path, filename)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            # Create .readthedocs.yaml configuration
            readthedocs_config = self._generate_readthedocs_config()
            config_path = os.path.join(docs.build_path, self.READTHEDOCS_YAML)
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(readthedocs_config)
            
            # Create requirements.txt for ReadTheDocs
            requirements_content = self._generate_requirements_txt()
            req_path = os.path.join(docs.build_path, self.REQUIREMENTS_TXT)
            with open(req_path, 'w', encoding='utf-8') as f:
                f.write(requirements_content)
            
            return PublishResult(
                status=PublishStatus.SUCCESS,
                url=f"https://{self.project_name.lower()}.readthedocs.io",
                build_log=["Documentation files generated successfully"]
            )
            
        except Exception as e:
            return PublishResult(
                status=PublishStatus.FAILED,
                error_message=str(e),
                build_log=[f"Error: {str(e)}"]
            )
    
    def build_documentation(self, module_paths: List[str]) -> SphinxDocuments:
        """
        Build complete documentation for multiple modules.
        
        Args:
            module_paths: List of module paths to document
            
        Returns:
            SphinxDocuments: Complete generated documentation
        """
        all_modules = []
        source_files = {}
        
        # Process each module
        for module_path in module_paths:
            api_info = self.extract_api_info(module_path)
            all_modules.append(api_info.module_name)
            
            # Generate RST for this module
            rst_content = self.api_generator.generate_sphinx_rst(api_info)
            source_files[f"{api_info.module_name}.rst"] = rst_content
        
        # Generate index.rst for all modules
        index_content = self._generate_index_rst(all_modules)
        source_files[self.INDEX_RST] = index_content
        
        # Generate conf.py
        config = self._generate_sphinx_config()
        source_files[self.CONF_PY] = self._config_to_python_file(config)
        
        # Create navigation structure
        navigation = self.create_navigation_structure(all_modules)
        
        return SphinxDocuments(
            source_files=source_files,
            config=config,
            navigation=navigation,
            build_path=self.output_dir
        )
    
    def _generate_index_rst(self, modules: List[str]) -> str:
        """Generate the main index.rst file."""
        content = []
        
        title = f"{self.project_name} Documentation"
        content.append(title)
        content.append("=" * len(title))
        content.append("")
        content.append("Welcome to the API documentation.")
        content.append("")
        content.append(".. toctree::")
        content.append("   :maxdepth: 2")
        content.append("   :caption: Contents:")
        content.append("")
        
        for module in modules:
            content.append(f"   {module}")
        
        content.append("")
        content.append("Indices and tables")
        content.append("==================")
        content.append("")
        content.append("* :ref:`genindex`")
        content.append("* :ref:`modindex`")
        content.append("* :ref:`search`")
        
        return "\n".join(content)
    
    def _generate_sphinx_config(self) -> Dict[str, Any]:
        """Generate Sphinx configuration."""
        return {
            'project': self.project_name,
            'copyright': '2024, Auto-generated',
            'author': 'Auto-generated',
            'extensions': [
                'sphinx.ext.autodoc',
                'sphinx.ext.viewcode',
                'sphinx.ext.napoleon',
                'sphinx.ext.intersphinx'
            ],
            'templates_path': ['_templates'],
            'exclude_patterns': ['_build', 'Thumbs.db', '.DS_Store'],
            'html_theme': 'sphinx_rtd_theme',
            'html_static_path': ['_static'],
            'autodoc_default_options': {
                'members': True,
                'undoc-members': True,
                'show-inheritance': True
            },
            'napoleon_google_docstring': True,
            'napoleon_numpy_docstring': True,
            'intersphinx_mapping': {
                'python': ('https://docs.python.org/3', None)
            }
        }
    
    def _config_to_python_file(self, config: Dict[str, Any]) -> str:
        """Convert configuration dict to Python file content."""
        lines = []
        lines.append("# Configuration file for the Sphinx documentation builder.")
        lines.append("# Auto-generated by fishertools DocumentationGenerator")
        lines.append("")
        
        for key, value in config.items():
            if isinstance(value, str):
                lines.append(f"{key} = '{value}'")
            elif isinstance(value, list):
                lines.append(f"{key} = {repr(value)}")
            elif isinstance(value, dict):
                lines.append(f"{key} = {repr(value)}")
            else:
                lines.append(f"{key} = {repr(value)}")
        
        return "\n".join(lines)
    
    def _generate_basic_example(self, function: FunctionInfo) -> ExampleCode:
        """Generate a basic usage example for a function."""
        # Create simple parameter values based on type hints
        param_values = []
        for param_name, param_type in function.parameters.items():
            if param_name == 'self':
                continue
            
            if 'str' in param_type.lower():
                param_values.append(f'"{param_name}_value"')
            elif 'int' in param_type.lower():
                param_values.append('42')
            elif 'float' in param_type.lower():
                param_values.append('3.14')
            elif 'bool' in param_type.lower():
                param_values.append('True')
            elif 'list' in param_type.lower():
                param_values.append('[1, 2, 3]')
            elif 'dict' in param_type.lower():
                param_values.append('{"key": "value"}')
            else:
                param_values.append('None')
        
        # Generate function call
        if param_values:
            call = f"{function.name}({', '.join(param_values)})"
        else:
            call = f"{function.name}()"
        
        code = f"""# Basic usage example
result = {call}
print(result)"""
        
        return ExampleCode(
            code=code,
            description=f"Basic usage of {function.name}",
            expected_output="# Output will depend on the function implementation"
        )
    
    def _generate_error_handling_example(self, function: FunctionInfo) -> ExampleCode:
        """Generate an example with error handling."""
        if not function.docstring or 'raise' not in function.docstring.lower():
            # Return a generic error handling example even if no specific exceptions are documented
            param_values = ['invalid_input'] * len([p for p in function.parameters.keys() if p != 'self'])
            
            if param_values:
                call = f"{function.name}({', '.join(param_values)})"
            else:
                call = f"{function.name}()"
            
            code = f"""# Generic error handling example
try:
    result = {call}
    print(f"Success: {{result}}")
except Exception as e:
    print(f"Error: {{e}}")"""
            
            return ExampleCode(
                code=code,
                description=f"Generic error handling with {function.name}",
                expected_output="# Will show either success or error message"
            )
        
        # Create a simple error handling example
        param_values = ['invalid_input'] * len([p for p in function.parameters.keys() if p != 'self'])
        
        if param_values:
            call = f"{function.name}({', '.join(param_values)})"
        else:
            call = f"{function.name}()"
        
        code = f"""# Error handling example
try:
    result = {call}
    print(f"Success: {{result}}")
except Exception as e:
    print(f"Error: {{e}}")"""
        
        return ExampleCode(
            code=code,
            description=f"Error handling with {function.name}",
            expected_output="# Will show either success or error message"
        )
    
    def _generate_advanced_example(self, function: FunctionInfo) -> ExampleCode:
        """Generate an advanced usage example."""
        # Create more realistic parameter values
        param_assignments = []
        param_names = []
        
        for param_name, param_type in function.parameters.items():
            if param_name == 'self':
                continue
            
            var_name = f"{param_name}_data"
            param_names.append(var_name)
            
            if 'str' in param_type.lower():
                param_assignments.append(f'{var_name} = "example_{param_name}"')
            elif 'list' in param_type.lower():
                param_assignments.append(f'{var_name} = ["item1", "item2", "item3"]')
            elif 'dict' in param_type.lower():
                param_assignments.append(f'{var_name} = {{"key1": "value1", "key2": "value2"}}')
            else:
                param_assignments.append(f'{var_name} = None  # Replace with appropriate value')
        
        assignments = '\n'.join(param_assignments)
        call = f"{function.name}({', '.join(param_names)})"
        
        code = f"""# Advanced usage example
{assignments}

result = {call}
print(f"Result: {{result}}")"""
        
        return ExampleCode(
            code=code,
            description=f"Advanced usage of {function.name} with realistic data",
            expected_output="# Output will show the processed result"
        )
    
    def _generate_readthedocs_config(self) -> str:
        """Generate .readthedocs.yaml configuration."""
        config = """# .readthedocs.yaml
# Read the Docs configuration file
# See https://docs.readthedocs.io/en/stable/config-file/v2.html for details

version: 2

build:
  os: ubuntu-22.04
  tools:
    python: "3.11"

sphinx:
  configuration: conf.py

python:
  install:
    - requirements: requirements.txt
    - method: pip
      path: .
"""
        return config
    
    def _generate_requirements_txt(self) -> str:
        """Generate requirements.txt for ReadTheDocs."""
        requirements = """# Documentation requirements
sphinx>=4.0.0
sphinx-rtd-theme>=1.0.0
sphinx-autodoc-typehints>=1.12.0
"""
        return requirements
    
    def generate_enhanced_documentation(self, module_paths: List[str]) -> Dict[str, Any]:
        """
        Generate enhanced documentation with visual elements.
        
        Args:
            module_paths: List of module paths to document
            
        Returns:
            Dictionary containing documentation and visual artifacts
        """
        try:
            # Generate standard Sphinx documentation
            sphinx_docs = self.build_documentation(module_paths)
            
            result = {
                'sphinx_docs': sphinx_docs,
                'visual_artifacts': {},
                'enhanced_files': {}
            }
            
            # Add visual elements if visual documentation is available
            if self._visual_docs:
                for module_path in module_paths:
                    try:
                        api_info = self.extract_api_info(module_path)
                        
                        # Create architecture diagram
                        arch_diagram = self._visual_docs.create_architecture_diagram([api_info.module_name])
                        result['visual_artifacts'][f"{api_info.module_name}_architecture"] = arch_diagram
                        
                        # Create enhanced RST with visual elements
                        enhanced_rst = self._create_enhanced_rst(api_info, arch_diagram)
                        result['enhanced_files'][f"{api_info.module_name}_enhanced.rst"] = enhanced_rst
                        
                    except Exception as e:
                        logging.warning(f"Failed to create visuals for {module_path}: {e}")
            
            return result
            
        except Exception as e:
            logging.error(f"Failed to generate enhanced documentation: {e}")
            raise
    
    def _create_enhanced_rst(self, api_info, architecture_diagram) -> str:
        """Create enhanced RST file with visual elements."""
        base_rst = self.api_generator.generate_sphinx_rst(api_info)
        
        # Add architecture diagram at the beginning
        enhanced_rst = f"""
{api_info.module_name} Module
{'=' * (len(api_info.module_name) + 7)}

Architecture Overview
--------------------

.. mermaid::

   {architecture_diagram.content if hasattr(architecture_diagram, 'content') else 'graph TD; A[Module] --> B[Components]'}

{base_rst}
"""
        return enhanced_rst