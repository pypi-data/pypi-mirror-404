"""
Unit tests for documentation structure and content.

Tests verify that all documentation files exist, contain required sections,
and have proper links and navigation.
"""

import os
import re
from pathlib import Path


class TestDocumentationStructure:
    """Test documentation file structure and existence."""

    def test_all_documentation_files_exist(self):
        """Test that all required documentation files exist in docs/ folder."""
        docs_dir = Path("docs")
        required_files = [
            "index.md",
            "getting-started.md",
            "features.md",
            "installation.md",
            "api-reference.md",
            "examples.md",
            "limitations.md",
            "contributing.md",
        ]
        
        for filename in required_files:
            filepath = docs_dir / filename
            assert filepath.exists(), f"Documentation file {filename} not found in docs/"
            assert filepath.is_file(), f"{filename} is not a file"

    def test_all_files_are_markdown(self):
        """Test that all documentation files have .md extension."""
        docs_dir = Path("docs")
        required_files = [
            "index.md",
            "getting-started.md",
            "features.md",
            "installation.md",
            "api-reference.md",
            "examples.md",
            "limitations.md",
            "contributing.md",
        ]
        
        for filename in required_files:
            assert filename.endswith(".md"), f"{filename} does not have .md extension"


class TestGettingStartedContent:
    """Test Getting Started documentation content."""

    def test_getting_started_contains_installation_section(self):
        """Test that Getting Started contains installation instructions."""
        with open("docs/getting-started.md", "r", encoding="utf-8") as f:
            content = f.read()
        
        assert "Installation" in content, "Getting Started missing Installation section"
        assert "pip install" in content, "Getting Started missing pip install command"

    def test_getting_started_contains_first_example(self):
        """Test that Getting Started contains a first example."""
        with open("docs/getting-started.md", "r", encoding="utf-8") as f:
            content = f.read()
        
        assert "example" in content.lower(), "Getting Started missing example"
        assert "```python" in content, "Getting Started missing code example"

    def test_getting_started_contains_links(self):
        """Test that Getting Started contains links to other sections."""
        with open("docs/getting-started.md", "r", encoding="utf-8") as f:
            content = f.read()
        
        assert "[Installation]" in content, "Getting Started missing link to Installation"
        assert "[Examples]" in content, "Getting Started missing link to Examples"
        assert "[Features]" in content, "Getting Started missing link to Features"


class TestFeaturesContent:
    """Test Features documentation content."""

    def test_features_contains_feature_list(self):
        """Test that Features contains a list of features."""
        with open("docs/features.md", "r", encoding="utf-8") as f:
            content = f.read()
        
        assert "Error Explanation" in content, "Features missing Error Explanation"
        assert "Safe Utilities" in content, "Features missing Safe Utilities"
        assert "Learning Tools" in content, "Features missing Learning Tools"

    def test_features_contains_descriptions(self):
        """Test that Features contains descriptions of each feature."""
        with open("docs/features.md", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check for feature descriptions
        assert "explain_error" in content, "Features missing explain_error description"
        assert "safe_get" in content, "Features missing safe_get description"


class TestInstallationContent:
    """Test Installation documentation content."""

    def test_installation_contains_system_requirements(self):
        """Test that Installation contains system requirements."""
        with open("docs/installation.md", "r", encoding="utf-8") as f:
            content = f.read()
        
        assert "Python" in content, "Installation missing Python requirement"
        assert "3.8" in content, "Installation missing Python version requirement"

    def test_installation_contains_os_specific_instructions(self):
        """Test that Installation contains instructions for different OS."""
        with open("docs/installation.md", "r", encoding="utf-8") as f:
            content = f.read()
        
        assert "Linux" in content, "Installation missing Linux instructions"
        assert "macOS" in content, "Installation missing macOS instructions"
        assert "Windows" in content, "Installation missing Windows instructions"

    def test_installation_contains_dependencies(self):
        """Test that Installation mentions dependencies."""
        with open("docs/installation.md", "r", encoding="utf-8") as f:
            content = f.read()
        
        assert "requests" in content, "Installation missing requests dependency"
        assert "click" in content, "Installation missing click dependency"


class TestAPIReferenceContent:
    """Test API Reference documentation content."""

    def test_api_reference_contains_main_functions(self):
        """Test that API Reference documents main functions."""
        with open("docs/api-reference.md", "r", encoding="utf-8") as f:
            content = f.read()
        
        assert "explain_error" in content, "API Reference missing explain_error"
        assert "safe_get" in content, "API Reference missing safe_get"
        assert "explain" in content, "API Reference missing explain"

    def test_api_reference_contains_parameters(self):
        """Test that API Reference includes function parameters."""
        with open("docs/api-reference.md", "r", encoding="utf-8") as f:
            content = f.read()
        
        assert "Parameters" in content, "API Reference missing Parameters section"
        assert "Returns" in content, "API Reference missing Returns section"

    def test_api_reference_contains_examples(self):
        """Test that API Reference includes code examples."""
        with open("docs/api-reference.md", "r", encoding="utf-8") as f:
            content = f.read()
        
        assert "```python" in content, "API Reference missing code examples"
        assert "Example" in content, "API Reference missing Example section"


class TestExamplesContent:
    """Test Examples documentation content."""

    def test_examples_contains_code_examples(self):
        """Test that Examples contains code examples."""
        with open("docs/examples.md", "r", encoding="utf-8") as f:
            content = f.read()
        
        assert "```python" in content, "Examples missing Python code"
        assert "Example" in content, "Examples missing Example sections"

    def test_examples_contains_multiple_examples(self):
        """Test that Examples contains multiple examples."""
        with open("docs/examples.md", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Count example sections
        example_count = content.count("## Example")
        assert example_count >= 3, f"Examples should have at least 3 examples, found {example_count}"


class TestLimitationsContent:
    """Test Limitations documentation content."""

    def test_limitations_contains_limitation_list(self):
        """Test that Limitations contains a list of limitations."""
        with open("docs/limitations.md", "r", encoding="utf-8") as f:
            content = f.read()
        
        assert "SyntaxError" in content, "Limitations missing SyntaxError limitation"
        assert "OOP" in content or "Object-Oriented" in content, "Limitations missing OOP limitation"

    def test_limitations_contains_explanations(self):
        """Test that Limitations explains each limitation."""
        with open("docs/limitations.md", "r", encoding="utf-8") as f:
            content = f.read()
        
        assert "Problem" in content or "The Problem" in content, "Limitations missing problem descriptions"
        assert "Workaround" in content, "Limitations missing workarounds"


class TestContributingContent:
    """Test Contributing documentation content."""

    def test_contributing_contains_contribution_types(self):
        """Test that Contributing explains how to contribute."""
        with open("docs/contributing.md", "r", encoding="utf-8") as f:
            content = f.read()
        
        assert "Report bugs" in content or "bug" in content.lower(), "Contributing missing bug reporting info"
        assert "code" in content.lower(), "Contributing missing code contribution info"

    def test_contributing_contains_development_setup(self):
        """Test that Contributing includes development setup instructions."""
        with open("docs/contributing.md", "r", encoding="utf-8") as f:
            content = f.read()
        
        assert "Fork" in content, "Contributing missing fork instructions"
        assert "git clone" in content, "Contributing missing clone instructions"
        assert "pip install" in content, "Contributing missing installation instructions"

    def test_contributing_contains_testing_info(self):
        """Test that Contributing includes testing information."""
        with open("docs/contributing.md", "r", encoding="utf-8") as f:
            content = f.read()
        
        assert "pytest" in content, "Contributing missing pytest information"
        assert "test" in content.lower(), "Contributing missing testing information"


class TestDocumentationLinks:
    """Test that documentation links are properly formatted."""

    def test_index_contains_navigation_links(self):
        """Test that index.md contains links to all sections."""
        with open("docs/index.md", "r", encoding="utf-8") as f:
            content = f.read()
        
        required_links = [
            "getting-started.md",
            "features.md",
            "installation.md",
            "api-reference.md",
            "examples.md",
            "limitations.md",
            "contributing.md",
        ]
        
        for link in required_links:
            assert link in content, f"index.md missing link to {link}"

    def test_all_files_have_return_link(self):
        """Test that all documentation files have a link back to index."""
        docs_dir = Path("docs")
        doc_files = [
            "getting-started.md",
            "features.md",
            "installation.md",
            "api-reference.md",
            "examples.md",
            "limitations.md",
            "contributing.md",
        ]
        
        for filename in doc_files:
            with open(docs_dir / filename, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Check for link back to index or documentation
            has_return_link = (
                "index.md" in content or
                "Documentation Index" in content or
                "Return to" in content
            )
            assert has_return_link, f"{filename} missing return link to index"


class TestREADMEContent:
    """Test main README.md content."""

    def test_readme_contains_brief_description(self):
        """Test that README contains a brief project description."""
        with open("README.md", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check for project description
        assert "Fishertools" in content or "fishertools" in content, "README missing project name"
        assert "Python" in content, "README missing Python mention"

    def test_readme_contains_quick_install(self):
        """Test that README contains quick installation instructions."""
        with open("README.md", "r", encoding="utf-8") as f:
            content = f.read()
        
        assert "pip install" in content, "README missing pip install command"

    def test_readme_contains_documentation_links(self):
        """Test that README contains links to documentation sections."""
        with open("README.md", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check for links to docs
        assert "docs/" in content or "documentation" in content.lower(), "README missing links to documentation"


class TestDocumentationConsistency:
    """Test consistency across documentation files."""

    def test_all_files_have_proper_headings(self):
        """Test that all documentation files have proper markdown headings."""
        docs_dir = Path("docs")
        doc_files = [
            "index.md",
            "getting-started.md",
            "features.md",
            "installation.md",
            "api-reference.md",
            "examples.md",
            "limitations.md",
            "contributing.md",
        ]
        
        for filename in doc_files:
            with open(docs_dir / filename, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Check for at least one heading
            assert "#" in content, f"{filename} missing markdown headings"
            assert content.startswith("#"), f"{filename} should start with a heading"

    def test_all_files_are_not_empty(self):
        """Test that all documentation files have content."""
        docs_dir = Path("docs")
        doc_files = [
            "index.md",
            "getting-started.md",
            "features.md",
            "installation.md",
            "api-reference.md",
            "examples.md",
            "limitations.md",
            "contributing.md",
        ]
        
        for filename in doc_files:
            filepath = docs_dir / filename
            size = filepath.stat().st_size
            assert size > 100, f"{filename} is too small (likely empty or minimal)"
