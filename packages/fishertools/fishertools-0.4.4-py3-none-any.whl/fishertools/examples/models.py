"""
Data models for the Example Repository module.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum


class ExampleCategory(Enum):
    """Categories of code examples."""
    COLLECTIONS = "collections"
    USER_INPUT = "user_input"
    FILE_OPERATIONS = "file_operations"
    ERROR_HANDLING = "error_handling"
    SIMPLE_PROJECTS = "simple_projects"
    BASIC_SYNTAX = "basic_syntax"


class ProjectType(Enum):
    """Types of simple projects."""
    CALCULATOR = "calculator"
    TODO_LIST = "todo_list"
    GUESSING_GAME = "guessing_game"
    TEXT_ANALYZER = "text_analyzer"
    FILE_ORGANIZER = "file_organizer"


@dataclass
class CodeExample:
    """A code example with explanation."""
    id: str
    title: str
    description: str
    code: str
    explanation: str
    difficulty: str
    topics: List[str]
    prerequisites: List[str]
    category: ExampleCategory
    expected_output: Optional[str] = None
    common_mistakes: List[str] = None
    
    def __post_init__(self):
        if self.common_mistakes is None:
            self.common_mistakes = []


@dataclass
class LineExplanation:
    """Explanation for a single line of code."""
    line_number: int
    code: str
    explanation: str
    concepts: List[str] = None
    
    def __post_init__(self):
        if self.concepts is None:
            self.concepts = []


@dataclass
class LineByLineExplanation:
    """Complete line-by-line explanation of code."""
    example_id: str
    title: str
    lines: List[LineExplanation]
    summary: str
    key_concepts: List[str] = None
    
    def __post_init__(self):
        if self.key_concepts is None:
            self.key_concepts = []


@dataclass
class ProjectStep:
    """A step in a project template."""
    step_number: int
    title: str
    description: str
    code_snippet: Optional[str] = None
    explanation: Optional[str] = None
    hints: List[str] = None
    
    def __post_init__(self):
        if self.hints is None:
            self.hints = []


@dataclass
class ProjectTemplate:
    """Template for a simple project."""
    id: str
    title: str
    description: str
    project_type: ProjectType
    difficulty: str
    estimated_time: int  # in minutes
    steps: List[ProjectStep]
    final_code: str
    extensions: List[str] = None  # suggested improvements
    
    def __post_init__(self):
        if self.extensions is None:
            self.extensions = []


@dataclass
class Scenario:
    """A learning scenario combining multiple examples."""
    id: str
    title: str
    description: str
    examples: List[CodeExample]
    learning_objectives: List[str]
    difficulty: str
    estimated_time: int  # in minutes