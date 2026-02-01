"""
Property-based tests for documentation structure and correctness.

These tests verify universal properties that should hold across all documentation files.
Uses Hypothesis for property-based testing.
"""

import re
from pathlib import Path
from hypothesis import given, strategies as st


class TestDocumentationProperties:
    """Property-based tests for documentation correctness."""

    @given(st.just(None))
    def test_property_1_all_sections_created(self, _):
        """
        **Validates: Requirements 1.1, 1.3**
        
        Property 1: All documentation sections are created
        For each of the 7 required sections (Getting Started, Features, Installation, 
        API Reference, Examples, Limitations, Contributing), the corresponding file 
        should exist in docs/ folder with .md extension.
        """
        docs_dir = Path("docs")
        required_sections = [
            "getting-started.md",
            "features.md",
            "installation.md",
            "api-reference.md",
            "examples.md",
            "limitations.md",
            "contributing.md",
        ]
        
        for section_file in required_sections:
            filepath = docs_dir / section_file
            assert filepath.exists(), f"Section file {section_file} does not exist"
            assert filepath.suffix == ".md", f"Section file {section_file} is not markdown"

    @given(st.just(None))
    def test_property_2_all_sections_linked_from_readme(self, _):
        """
        **Validates: Requirements 2.3, 3.3, 4.3, 5.3, 6.3, 7.3, 8.3, 9.3, 11.3**
        
        Property 2: All sections are accessible by links from README
        For each of the 7 documentation sections in docs/, the main README.md 
        should contain a working link to that section.
        """
        with open("README.md", "r", encoding="utf-8") as f:
            readme_content = f.read()
        
        required_links = [
            "docs/getting-started.md",
            "docs/features.md",
            "docs/installation.md",
            "docs/api-reference.md",
            "docs/examples.md",
            "docs/limitations.md",
            "docs/contributing.md",
        ]
        
        for link in required_links:
            assert link in readme_content, f"README missing link to {link}"

    @given(st.just(None))
    def test_property_3_all_links_work(self, _):
        """
        **Validates: Requirements 11.1, 11.2**
        
        Property 3: All links in documentation work
        For any link in documentation files (in docs/ and main README), 
        that link should point to an existing file or section.
        """
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
        
        # Pattern to find markdown links: [text](path)
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        
        for filename in doc_files:
            filepath = docs_dir / filename
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Find all links
            links = re.findall(link_pattern, content)
            
            for link_text, link_path in links:
                # Skip external links (http, https, mailto)
                if link_path.startswith(('http://', 'https://', 'mailto:')):
                    continue
                
                # Skip anchor-only links
                if link_path.startswith('#'):
                    continue
                
                # Check if file exists
                    target_path = Path(filepath.parent) / link_path
                
                # Normalize path
                target_path = target_path.resolve()
                
                # For links like "index.md", check if file exists
                if not link_path.startswith('#'):
                    assert target_path.exists() or target_path.with_suffix('').exists(), \
                        f"Link {link_path} in {filename} points to non-existent file"

    @given(st.just(None))
    def test_property_4_readme_brief_description(self, _):
        """
        **Validates: Requirements 9.1**
        
        Property 4: Main README contains brief description
        For the main README.md, the project description should contain 
        no more than 50 words.
        """
        with open("README.md", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Extract the main description (first paragraph after title)
        lines = content.split('\n')
        description_lines = []
        in_description = False
        
        for line in lines:
            if line.startswith('# '):
                in_description = True
                continue
            if in_description:
                if line.startswith('##') or line.startswith('```'):
                    break
                if line.strip():
                    description_lines.append(line)
        
        description = ' '.join(description_lines).strip()
        word_count = len(description.split())
        
        assert word_count <= 50, f"README description has {word_count} words, should be <= 50"

    @given(st.just(None))
    def test_property_5_readme_contains_all_section_links(self, _):
        """
        **Validates: Requirements 9.3, 11.3**
        
        Property 5: Main README contains links to all sections
        For the main README.md, it should contain links to all 7 documentation 
        sections (Getting Started, Features, Installation, API Reference, 
        Examples, Limitations, Contributing).
        """
        with open("README.md", "r", encoding="utf-8") as f:
            content = f.read()
        
        required_sections = [
            "Getting Started",
            "Features",
            "Installation",
            "API Reference",
            "Examples",
            "Limitations",
            "Contributing",
        ]
        
        for section in required_sections:
            assert section in content, f"README missing reference to {section}"

    @given(st.just(None))
    def test_property_6_each_section_links_to_index(self, _):
        """
        **Validates: Requirements 11.4**
        
        Property 6: Each section contains link to main page
        For each file in docs/ folder, that file should contain a link to 
        the main documentation page (index.md or README.md).
        """
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
            filepath = docs_dir / filename
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Check for link back to index or documentation
            has_return_link = (
                "index.md" in content or
                "Documentation Index" in content or
                "Return to" in content or
                "Back to" in content
            )
            assert has_return_link, f"{filename} missing return link to index"

    @given(st.just(None))
    def test_property_7_readme_no_duplication(self, _):
        """
        **Validates: Requirements 9.5, 10.3**
        
        Property 7: Main README contains no duplicated information
        For the main README.md, it should contain only brief information and links, 
        without detailed sections that are in docs/.
        """
        with open("README.md", "r", encoding="utf-8") as f:
            readme_content = f.read()
        
        # Check that README doesn't contain detailed sections
        # that should be in docs/
        detailed_sections = [
            "🚨 Объяснение ошибок",  # Russian
            "🛡️ Безопасные утилиты",  # Russian
            "📚 Обучающие инструменты",  # Russian
            "🔧 Готовые паттерны",  # Russian
            "## 🎯 Основные возможности",  # Russian
            "### 🚨 Объяснение ошибок Python",  # Russian
        ]
        
        # Count how many detailed sections are in README
        detailed_count = sum(1 for section in detailed_sections if section in readme_content)
        
        # README should have minimal detailed content (mostly links)
        # Allow some basic feature descriptions but not full sections
        assert detailed_count == 0, f"README contains {detailed_count} detailed sections that should be in docs/"

    @given(st.just(None))
    def test_property_all_files_have_content(self, _):
        """
        Property: All documentation files have substantial content
        For each documentation file, it should have more than 100 bytes of content.
        """
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
            assert size > 100, f"{filename} is too small ({size} bytes)"

    @given(st.just(None))
    def test_property_all_files_have_headings(self, _):
        """
        Property: All documentation files have proper markdown headings
        For each documentation file, it should start with a markdown heading.
        """
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
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            assert content.startswith("#"), f"{filename} should start with a markdown heading"
            assert "#" in content, f"{filename} should contain markdown headings"

    @given(st.just(None))
    def test_property_index_has_navigation(self, _):
        """
        Property: Index page has navigation to all sections
        The index.md file should contain links to all 7 documentation sections.
        """
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

    @given(st.just(None))
    def test_property_readme_has_quick_reference(self, _):
        """
        Property: README has quick reference table
        The main README.md should contain a quick reference table with functions.
        """
        with open("README.md", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check for table structure
        assert "|" in content, "README missing table structure"
        assert "explain_error" in content, "README missing explain_error in quick reference"
        assert "safe_get" in content, "README missing safe_get in quick reference"
