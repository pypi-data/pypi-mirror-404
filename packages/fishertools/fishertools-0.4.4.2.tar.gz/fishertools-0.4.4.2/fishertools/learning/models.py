"""
Data models for the Learning System module.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Any, Dict, Literal
from enum import Enum


class DifficultyLevel(Enum):
    """Difficulty levels for learning content."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class ExerciseStatus(Enum):
    """Status of an interactive exercise."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class CodeContext:
    """Context information for code analysis."""
    file_path: Optional[str] = None
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    imports: List[str] = None
    variables: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.imports is None:
            self.imports = []
        if self.variables is None:
            self.variables = {}


@dataclass
class StepExplanation:
    """Detailed explanation of a single code step."""
    step_number: int
    description: str
    code_snippet: str
    input_example: Optional[str] = None
    output_example: Optional[str] = None
    related_concepts: List[str] = None
    visual_aid: Optional[str] = None
    
    def __post_init__(self):
        if self.related_concepts is None:
            self.related_concepts = []


@dataclass
class ValidationResult:
    """Result of validating an exercise solution."""
    is_correct: bool
    feedback: str
    errors: List[str] = None
    suggestions: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.suggestions is None:
            self.suggestions = []


@dataclass
class InteractiveExercise:
    """An interactive coding exercise."""
    id: str
    title: str
    description: str
    starter_code: str
    expected_output: str
    hints: List[str]
    difficulty_level: DifficultyLevel
    topic: str
    status: ExerciseStatus = ExerciseStatus.NOT_STARTED
    attempts: int = 0
    max_attempts: int = 3


@dataclass
class LearningProgress:
    """User's learning progress tracking."""
    user_id: str
    completed_topics: List[str]
    current_level: DifficultyLevel
    total_exercises_completed: int
    last_activity: datetime
    achievements: List[str]
    session_count: int = 0
    total_time_spent: int = 0  # in minutes


@dataclass
class TutorialSession:
    """A tutorial learning session."""
    session_id: str
    topic: str
    level: DifficultyLevel
    start_time: datetime
    exercises: List[InteractiveExercise]
    current_exercise_index: int = 0
    is_completed: bool = False
    end_time: Optional[datetime] = None