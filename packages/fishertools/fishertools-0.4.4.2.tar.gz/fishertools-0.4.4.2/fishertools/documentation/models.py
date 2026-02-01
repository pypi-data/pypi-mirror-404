"""
Data models for the Documentation Generation module and Extended Documentation system.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class DiagramType(Enum):
    """Types of diagrams that can be generated."""
    ARCHITECTURE = "architecture"
    DATA_FLOW = "data_flow"
    FLOWCHART = "flowchart"
    STRUCTURE = "structure"


class PublishStatus(Enum):
    """Status of documentation publishing."""
    SUCCESS = "success"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"
    PENDING = "pending"


@dataclass
class FunctionInfo:
    """Information about a function for documentation."""
    name: str
    docstring: Optional[str]
    parameters: Dict[str, str]  # param_name -> type_annotation
    return_type: Optional[str]
    module_path: str
    line_number: int
    examples: Optional[List[str]] = None

    def __post_init__(self):
        if self.examples is None:
            self.examples = []


@dataclass
class APIInfo:
    """Complete API information for a module."""
    module_name: str
    functions: List[FunctionInfo]
    classes: List[Dict[str, Any]]
    constants: Dict[str, Any]
    imports: List[str]
    docstring: Optional[str] = None


@dataclass
class NavigationTree:
    """Navigation structure for documentation."""
    name: str
    path: str
    children: List['NavigationTree'] = None

    def __post_init__(self):
        if self.children is None:
            self.children = []


@dataclass
class ExampleCode:
    """Code example with explanation."""
    code: str
    description: str
    expected_output: Optional[str] = None
    language: str = "python"


@dataclass
class SphinxDocuments:
    """Generated Sphinx documentation."""
    source_files: Dict[str, str]  # filename -> content
    config: Dict[str, Any]
    navigation: NavigationTree
    build_path: str


@dataclass
class PublishResult:
    """Result of publishing documentation."""
    status: PublishStatus
    url: Optional[str] = None
    error_message: Optional[str] = None
    build_log: Optional[List[str]] = None

    def __post_init__(self):
        if self.build_log is None:
            self.build_log = []


@dataclass
class MermaidDiagram:
    """Mermaid diagram representation."""
    diagram_type: DiagramType
    content: str
    title: Optional[str] = None


@dataclass
class FlowDiagram:
    """Data flow diagram."""
    nodes: List[Dict[str, str]]
    edges: List[Dict[str, str]]
    title: str


@dataclass
class Flowchart:
    """Algorithm flowchart."""
    steps: List[Dict[str, Any]]
    connections: List[Dict[str, str]]
    title: str


@dataclass
class StructureDiagram:
    """Data structure visualization."""
    structure_type: str
    data: Any
    visualization: str
    title: Optional[str] = None


# Extended Documentation System Models


@dataclass
class CodeExample:
    """Represents a single code example."""
    id: str
    module: str  # errors, safe, learn, patterns, config, documentation
    title: str
    code: str
    expected_output: str
    explanation: str
    variations: List[str] = field(default_factory=list)
    difficulty: str = "beginner"  # beginner, intermediate, advanced
    tags: List[str] = field(default_factory=list)


@dataclass
class Diagram:
    """Represents a diagram."""
    id: str
    title: str
    type: str  # architecture, flow, concept
    modules: List[str] = field(default_factory=list)
    description: str = ""
    content: str = ""  # Mermaid or SVG
    labels: Dict[str, str] = field(default_factory=dict)
    legend: str = ""


@dataclass
class FAQEntry:
    """Represents a FAQ entry."""
    id: str
    question: str
    answer: str
    topic: str  # module or topic name
    code_example: Optional[str] = None
    related_entries: List[str] = field(default_factory=list)
    difficulty: str = "beginner"  # beginner, intermediate, advanced
    tags: List[str] = field(default_factory=list)


@dataclass
class GuideSection:
    """Represents a section in a guide."""
    id: str
    title: str
    content: str
    difficulty: str = "beginner"  # beginner, intermediate, advanced
    estimated_time: int = 0  # minutes
    exercises: List[str] = field(default_factory=list)
    checkpoints: List[str] = field(default_factory=list)
    code_examples: List[str] = field(default_factory=list)


@dataclass
class Guide:
    """Represents a complete guide."""
    id: str
    module: str
    title: str
    description: str = ""
    prerequisites: List[str] = field(default_factory=list)
    sections: List[GuideSection] = field(default_factory=list)
    reading_order: List[str] = field(default_factory=list)


@dataclass
class Practice:
    """Represents a best practice."""
    id: str
    title: str
    category: str  # error_handling, safety, learning
    module: str
    description: str = ""
    correct_example: str = ""
    incorrect_example: str = ""
    explanation: str = ""
    performance_notes: Optional[str] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class TroubleshootingEntry:
    """Represents a troubleshooting entry."""
    id: str
    error_type: str
    title: str
    description: str = ""
    cause: str = ""
    solution: str = ""
    step_by_step: List[str] = field(default_factory=list)
    prevention: str = ""
    module: str = ""
    related_entries: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


@dataclass
class NavigationNode:
    """Represents a navigation node."""
    id: str
    title: str
    path: str
    parent: Optional[str] = None
    children: List[str] = field(default_factory=list)
    type: str = ""  # guide, example, faq, practice, troubleshooting


@dataclass
class ValidationResult:
    """Represents validation result."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
