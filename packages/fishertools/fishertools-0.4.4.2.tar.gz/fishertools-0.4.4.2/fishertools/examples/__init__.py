"""
Example Repository Module

Manages collections of examples and scenarios for Python beginners.
Provides categorized examples with step-by-step explanations.
"""

from .repository import ExampleRepository
from .models import (
    CodeExample,
    Scenario,
    ProjectTemplate,
    LineByLineExplanation
)

__all__ = [
    "ExampleRepository",
    "CodeExample",
    "Scenario", 
    "ProjectTemplate",
    "LineByLineExplanation"
]