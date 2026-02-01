"""Tests for extended documentation manager interfaces."""

import pytest
from fishertools.documentation.managers import (
    ExamplesManager,
    DiagramsManager,
    FAQManager,
    GuidesManager,
    BestPracticesManager,
    TroubleshootingManager,
    NavigationManager,
    ContentValidator,
)


class TestManagerInterfaces:
    """Tests for manager interface definitions."""

    def test_examples_manager_interface_exists(self):
        """Test that ExamplesManager interface exists."""
        assert hasattr(ExamplesManager, "add_example")
        assert hasattr(ExamplesManager, "get_examples_by_module")
        assert hasattr(ExamplesManager, "get_example")
        assert hasattr(ExamplesManager, "list_all_examples")
        assert hasattr(ExamplesManager, "validate_example")

    def test_diagrams_manager_interface_exists(self):
        """Test that DiagramsManager interface exists."""
        assert hasattr(DiagramsManager, "add_diagram")
        assert hasattr(DiagramsManager, "get_diagrams_by_module")
        assert hasattr(DiagramsManager, "get_diagrams_by_type")
        assert hasattr(DiagramsManager, "list_all_diagrams")
        assert hasattr(DiagramsManager, "validate_diagram")

    def test_faq_manager_interface_exists(self):
        """Test that FAQManager interface exists."""
        assert hasattr(FAQManager, "add_entry")
        assert hasattr(FAQManager, "get_entries_by_topic")
        assert hasattr(FAQManager, "search_entries")
        assert hasattr(FAQManager, "get_entry")
        assert hasattr(FAQManager, "list_all_entries")
        assert hasattr(FAQManager, "get_topic_count")

    def test_guides_manager_interface_exists(self):
        """Test that GuidesManager interface exists."""
        assert hasattr(GuidesManager, "add_guide")
        assert hasattr(GuidesManager, "get_guide")
        assert hasattr(GuidesManager, "get_all_guides")
        assert hasattr(GuidesManager, "get_guide_section")
        assert hasattr(GuidesManager, "validate_guide")

    def test_best_practices_manager_interface_exists(self):
        """Test that BestPracticesManager interface exists."""
        assert hasattr(BestPracticesManager, "add_practice")
        assert hasattr(BestPracticesManager, "get_practices_by_category")
        assert hasattr(BestPracticesManager, "get_practices_by_module")
        assert hasattr(BestPracticesManager, "get_all_practices")
        assert hasattr(BestPracticesManager, "validate_practice")

    def test_troubleshooting_manager_interface_exists(self):
        """Test that TroubleshootingManager interface exists."""
        assert hasattr(TroubleshootingManager, "add_entry")
        assert hasattr(TroubleshootingManager, "get_entries_by_module")
        assert hasattr(TroubleshootingManager, "get_entries_by_error_type")
        assert hasattr(TroubleshootingManager, "search_entries")
        assert hasattr(TroubleshootingManager, "get_entry")
        assert hasattr(TroubleshootingManager, "list_all_entries")

    def test_navigation_manager_interface_exists(self):
        """Test that NavigationManager interface exists."""
        assert hasattr(NavigationManager, "add_node")
        assert hasattr(NavigationManager, "get_breadcrumbs")
        assert hasattr(NavigationManager, "get_next_node")
        assert hasattr(NavigationManager, "get_previous_node")
        assert hasattr(NavigationManager, "get_related_nodes")
        assert hasattr(NavigationManager, "generate_table_of_contents")
        assert hasattr(NavigationManager, "validate_links")

    def test_content_validator_interface_exists(self):
        """Test that ContentValidator interface exists."""
        assert hasattr(ContentValidator, "validate_code_syntax")
        assert hasattr(ContentValidator, "validate_code_execution")
        assert hasattr(ContentValidator, "validate_completeness")
        assert hasattr(ContentValidator, "validate_consistency")
        assert hasattr(ContentValidator, "validate_links")
        assert hasattr(ContentValidator, "validate_accessibility")
