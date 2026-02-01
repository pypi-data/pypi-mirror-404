"""Manager interfaces for extended documentation system."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from fishertools.documentation.models import (
    CodeExample,
    Diagram,
    FAQEntry,
    Guide,
    Practice,
    TroubleshootingEntry,
    NavigationNode,
    ValidationResult,
)


class ExamplesManager(ABC):
    """Manages code examples."""

    @abstractmethod
    def add_example(self, example: CodeExample) -> None:
        """Add a code example."""
        pass

    @abstractmethod
    def get_examples_by_module(self, module: str) -> List[CodeExample]:
        """Get all examples for a module."""
        pass

    @abstractmethod
    def get_example(self, id: str) -> Optional[CodeExample]:
        """Get a specific example by ID."""
        pass

    @abstractmethod
    def list_all_examples(self) -> List[CodeExample]:
        """List all examples."""
        pass

    @abstractmethod
    def validate_example(self, example: CodeExample) -> ValidationResult:
        """Validate a code example."""
        pass


class DiagramsManager(ABC):
    """Manages diagrams."""

    @abstractmethod
    def add_diagram(self, diagram: Diagram) -> None:
        """Add a diagram."""
        pass

    @abstractmethod
    def get_diagrams_by_module(self, module: str) -> List[Diagram]:
        """Get all diagrams for a module."""
        pass

    @abstractmethod
    def get_diagrams_by_type(self, type: str) -> List[Diagram]:
        """Get all diagrams of a specific type."""
        pass

    @abstractmethod
    def list_all_diagrams(self) -> List[Diagram]:
        """List all diagrams."""
        pass

    @abstractmethod
    def validate_diagram(self, diagram: Diagram) -> ValidationResult:
        """Validate a diagram."""
        pass


class FAQManager(ABC):
    """Manages FAQ entries."""

    @abstractmethod
    def add_entry(self, entry: FAQEntry) -> None:
        """Add a FAQ entry."""
        pass

    @abstractmethod
    def get_entries_by_topic(self, topic: str) -> List[FAQEntry]:
        """Get all entries for a topic."""
        pass

    @abstractmethod
    def search_entries(self, query: str) -> List[FAQEntry]:
        """Search FAQ entries."""
        pass

    @abstractmethod
    def get_entry(self, id: str) -> Optional[FAQEntry]:
        """Get a specific entry by ID."""
        pass

    @abstractmethod
    def list_all_entries(self) -> List[FAQEntry]:
        """List all FAQ entries."""
        pass

    @abstractmethod
    def get_topic_count(self, topic: str) -> int:
        """Get count of entries for a topic."""
        pass


class GuidesManager(ABC):
    """Manages guides."""

    @abstractmethod
    def add_guide(self, guide: Guide) -> None:
        """Add a guide."""
        pass

    @abstractmethod
    def get_guide(self, module: str) -> Optional[Guide]:
        """Get a guide for a module."""
        pass

    @abstractmethod
    def get_all_guides(self) -> List[Guide]:
        """Get all guides."""
        pass

    @abstractmethod
    def get_guide_section(self, guide_id: str, section_id: str) -> Optional[object]:
        """Get a specific section from a guide."""
        pass

    @abstractmethod
    def validate_guide(self, guide: Guide) -> ValidationResult:
        """Validate a guide."""
        pass


class BestPracticesManager(ABC):
    """Manages best practices."""

    @abstractmethod
    def add_practice(self, practice: Practice) -> None:
        """Add a best practice."""
        pass

    @abstractmethod
    def get_practices_by_category(self, category: str) -> List[Practice]:
        """Get all practices for a category."""
        pass

    @abstractmethod
    def get_practices_by_module(self, module: str) -> List[Practice]:
        """Get all practices for a module."""
        pass

    @abstractmethod
    def get_all_practices(self) -> List[Practice]:
        """Get all practices."""
        pass

    @abstractmethod
    def validate_practice(self, practice: Practice) -> ValidationResult:
        """Validate a practice."""
        pass


class TroubleshootingManager(ABC):
    """Manages troubleshooting entries."""

    @abstractmethod
    def add_entry(self, entry: TroubleshootingEntry) -> None:
        """Add a troubleshooting entry."""
        pass

    @abstractmethod
    def get_entries_by_module(self, module: str) -> List[TroubleshootingEntry]:
        """Get all entries for a module."""
        pass

    @abstractmethod
    def get_entries_by_error_type(self, error_type: str) -> List[TroubleshootingEntry]:
        """Get all entries for an error type."""
        pass

    @abstractmethod
    def search_entries(self, query: str) -> List[TroubleshootingEntry]:
        """Search troubleshooting entries."""
        pass

    @abstractmethod
    def get_entry(self, id: str) -> Optional[TroubleshootingEntry]:
        """Get a specific entry by ID."""
        pass

    @abstractmethod
    def list_all_entries(self) -> List[TroubleshootingEntry]:
        """List all troubleshooting entries."""
        pass


class NavigationManager(ABC):
    """Manages navigation."""

    @abstractmethod
    def add_node(self, node: NavigationNode) -> None:
        """Add a navigation node."""
        pass

    @abstractmethod
    def get_breadcrumbs(self, node_id: str) -> List[NavigationNode]:
        """Get breadcrumb path for a node."""
        pass

    @abstractmethod
    def get_next_node(self, node_id: str) -> Optional[NavigationNode]:
        """Get next node in sequence."""
        pass

    @abstractmethod
    def get_previous_node(self, node_id: str) -> Optional[NavigationNode]:
        """Get previous node in sequence."""
        pass

    @abstractmethod
    def get_related_nodes(self, node_id: str) -> List[NavigationNode]:
        """Get related nodes."""
        pass

    @abstractmethod
    def generate_table_of_contents(self) -> str:
        """Generate table of contents."""
        pass

    @abstractmethod
    def validate_links(self) -> ValidationResult:
        """Validate all links."""
        pass


class ContentValidator(ABC):
    """Validates content."""

    @abstractmethod
    def validate_code_syntax(self, code: str) -> ValidationResult:
        """Validate code syntax."""
        pass

    @abstractmethod
    def validate_code_execution(
        self, code: str, python_versions: List[str]
    ) -> ValidationResult:
        """Validate code execution."""
        pass

    @abstractmethod
    def validate_completeness(self, content: Dict) -> ValidationResult:
        """Validate content completeness."""
        pass

    @abstractmethod
    def validate_consistency(self, content: Dict) -> ValidationResult:
        """Validate content consistency."""
        pass

    @abstractmethod
    def validate_links(self, content: Dict) -> ValidationResult:
        """Validate links."""
        pass

    @abstractmethod
    def validate_accessibility(self, content: Dict) -> ValidationResult:
        """Validate accessibility."""
        pass
