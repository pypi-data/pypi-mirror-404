"""Tests for extended documentation models and managers."""

import pytest
from fishertools.documentation.models import (
    CodeExample,
    Diagram,
    FAQEntry,
    Guide,
    GuideSection,
    Practice,
    TroubleshootingEntry,
    NavigationNode,
    ValidationResult,
)


class TestCodeExample:
    """Tests for CodeExample model."""

    def test_create_code_example(self):
        """Test creating a code example."""
        example = CodeExample(
            id="ex-1",
            module="errors",
            title="Error Handling",
            code="print('hello')",
            expected_output="hello",
            explanation="This prints hello",
        )
        assert example.id == "ex-1"
        assert example.module == "errors"
        assert example.title == "Error Handling"
        assert example.code == "print('hello')"
        assert example.expected_output == "hello"
        assert example.explanation == "This prints hello"
        assert example.difficulty == "beginner"
        assert example.variations == []
        assert example.tags == []

    def test_code_example_with_variations(self):
        """Test code example with variations."""
        example = CodeExample(
            id="ex-2",
            module="safe",
            title="Safe Division",
            code="result = 10 / 2",
            expected_output="5",
            explanation="Safe division",
            variations=["10 / 0", "10.5 / 2.5"],
            tags=["division", "math"],
        )
        assert len(example.variations) == 2
        assert len(example.tags) == 2


class TestDiagram:
    """Tests for Diagram model."""

    def test_create_diagram(self):
        """Test creating a diagram."""
        diagram = Diagram(
            id="diag-1",
            title="Architecture",
            type="architecture",
            description="System architecture",
        )
        assert diagram.id == "diag-1"
        assert diagram.title == "Architecture"
        assert diagram.type == "architecture"
        assert diagram.modules == []
        assert diagram.labels == {}

    def test_diagram_with_modules(self):
        """Test diagram with modules."""
        diagram = Diagram(
            id="diag-2",
            title="Module Relationships",
            type="flow",
            modules=["errors", "safe", "learn"],
            labels={"node1": "Error Handler", "node2": "Safe Module"},
            legend="Nodes represent modules",
        )
        assert len(diagram.modules) == 3
        assert len(diagram.labels) == 2
        assert diagram.legend == "Nodes represent modules"


class TestFAQEntry:
    """Tests for FAQEntry model."""

    def test_create_faq_entry(self):
        """Test creating a FAQ entry."""
        entry = FAQEntry(
            id="faq-1",
            question="How do I handle errors?",
            answer="Use the error handling module",
            topic="errors",
        )
        assert entry.id == "faq-1"
        assert entry.question == "How do I handle errors?"
        assert entry.answer == "Use the error handling module"
        assert entry.topic == "errors"
        assert entry.code_example is None
        assert entry.related_entries == []

    def test_faq_entry_with_code(self):
        """Test FAQ entry with code example."""
        entry = FAQEntry(
            id="faq-2",
            question="How to use safe division?",
            answer="Use safe_divide function",
            topic="safe",
            code_example="safe_divide(10, 2)",
            tags=["division", "safety"],
        )
        assert entry.code_example == "safe_divide(10, 2)"
        assert len(entry.tags) == 2


class TestGuide:
    """Tests for Guide model."""

    def test_create_guide(self):
        """Test creating a guide."""
        section = GuideSection(
            id="sec-1",
            title="Introduction",
            content="Getting started",
            difficulty="beginner",
            estimated_time=15,
        )
        guide = Guide(
            id="guide-1",
            module="errors",
            title="Error Handling Guide",
            description="Learn error handling",
            sections=[section],
        )
        assert guide.id == "guide-1"
        assert guide.module == "errors"
        assert len(guide.sections) == 1
        assert guide.sections[0].title == "Introduction"

    def test_guide_section_with_exercises(self):
        """Test guide section with exercises."""
        section = GuideSection(
            id="sec-2",
            title="Practice",
            content="Practice exercises",
            exercises=["Exercise 1", "Exercise 2"],
            checkpoints=["Checkpoint 1"],
            code_examples=["example1.py"],
        )
        assert len(section.exercises) == 2
        assert len(section.checkpoints) == 1
        assert len(section.code_examples) == 1


class TestPractice:
    """Tests for Practice model."""

    def test_create_practice(self):
        """Test creating a best practice."""
        practice = Practice(
            id="prac-1",
            title="Error Handling Best Practice",
            category="error_handling",
            module="errors",
            description="Always handle errors",
            correct_example="try: ... except: ...",
            incorrect_example="# ignore errors",
            explanation="Proper error handling prevents crashes",
        )
        assert practice.id == "prac-1"
        assert practice.category == "error_handling"
        assert practice.module == "errors"
        assert practice.correct_example == "try: ... except: ..."


class TestTroubleshootingEntry:
    """Tests for TroubleshootingEntry model."""

    def test_create_troubleshooting_entry(self):
        """Test creating a troubleshooting entry."""
        entry = TroubleshootingEntry(
            id="ts-1",
            error_type="ValueError",
            title="Value Error",
            description="Handling value errors",
            cause="Invalid value provided",
            solution="Check input validation",
            module="errors",
        )
        assert entry.id == "ts-1"
        assert entry.error_type == "ValueError"
        assert entry.module == "errors"

    def test_troubleshooting_with_steps(self):
        """Test troubleshooting entry with step-by-step solution."""
        entry = TroubleshootingEntry(
            id="ts-2",
            error_type="TypeError",
            title="Type Error",
            step_by_step=["Step 1: Check types", "Step 2: Validate input"],
            prevention="Use type hints",
        )
        assert len(entry.step_by_step) == 2
        assert entry.prevention == "Use type hints"


class TestNavigationNode:
    """Tests for NavigationNode model."""

    def test_create_navigation_node(self):
        """Test creating a navigation node."""
        node = NavigationNode(
            id="nav-1",
            title="Home",
            path="/",
            type="guide",
        )
        assert node.id == "nav-1"
        assert node.title == "Home"
        assert node.path == "/"
        assert node.parent is None
        assert node.children == []

    def test_navigation_node_with_hierarchy(self):
        """Test navigation node with parent and children."""
        node = NavigationNode(
            id="nav-2",
            title="Guides",
            path="/guides",
            parent="nav-1",
            children=["nav-3", "nav-4"],
        )
        assert node.parent == "nav-1"
        assert len(node.children) == 2


class TestValidationResult:
    """Tests for ValidationResult model."""

    def test_valid_result(self):
        """Test valid validation result."""
        result = ValidationResult(is_valid=True)
        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == []

    def test_invalid_result_with_errors(self):
        """Test invalid validation result with errors."""
        result = ValidationResult(
            is_valid=False,
            errors=["Error 1", "Error 2"],
            warnings=["Warning 1"],
        )
        assert result.is_valid is False
        assert len(result.errors) == 2
        assert len(result.warnings) == 1
