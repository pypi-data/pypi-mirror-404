"""
Data models for the Configuration Management module.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Literal
from enum import Enum


class ConfigFormat(Enum):
    """Supported configuration file formats."""
    JSON = "json"
    YAML = "yaml"
    TOML = "toml"


class ErrorSeverity(Enum):
    """Severity levels for configuration errors."""
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class RecoveryStrategy(Enum):
    """Strategies for error recovery."""
    USE_DEFAULTS = "use_defaults"
    PROMPT_USER = "prompt_user"
    FAIL_GRACEFULLY = "fail_gracefully"
    RETRY = "retry"


@dataclass
class ConfigError:
    """Configuration error information."""
    message: str
    field_path: str
    severity: ErrorSeverity
    suggested_fix: Optional[str] = None
    line_number: Optional[int] = None


@dataclass
class ValidationResult:
    """Result of configuration validation."""
    is_valid: bool
    errors: Optional[List[ConfigError]] = None
    warnings: Optional[List[ConfigError]] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


@dataclass
class RecoveryAction:
    """Action to take for error recovery."""
    strategy: RecoveryStrategy
    message: str
    fallback_config: Optional[Dict[str, Any]] = None


@dataclass
class LearningConfig:
    """Configuration for the learning system."""
    # Basic settings
    default_level: Literal["beginner", "intermediate", "advanced"] = "beginner"
    explanation_verbosity: Literal["brief", "detailed", "comprehensive"] = "detailed"
    
    # Visual settings
    visual_aids_enabled: bool = True
    diagram_style: str = "modern"
    color_scheme: str = "default"
    
    # Progress and tracking
    progress_tracking_enabled: bool = True
    save_progress_locally: bool = True
    
    # Content and examples
    suggested_topics_count: int = 3
    max_examples_per_topic: int = 5
    exercise_difficulty_progression: Optional[List[str]] = None
    
    # Integration
    readthedocs_project: Optional[str] = None
    sphinx_theme: str = "sphinx_rtd_theme"
    
    # Advanced settings
    enable_interactive_sessions: bool = True
    session_timeout_minutes: int = 30
    max_hint_count: int = 3
    
    def __post_init__(self):
        if self.exercise_difficulty_progression is None:
            self.exercise_difficulty_progression = ["beginner", "intermediate", "advanced"]