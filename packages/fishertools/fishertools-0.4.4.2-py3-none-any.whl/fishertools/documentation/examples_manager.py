"""Concrete implementation of ExamplesManager for managing code examples."""

import json
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from fishertools.documentation.managers import ExamplesManager
from fishertools.documentation.models import CodeExample, ValidationResult


class FileBasedExamplesManager(ExamplesManager):
    """File-based implementation of ExamplesManager using JSON storage."""

    def __init__(self, storage_dir: str = "docs/interactive-examples"):
        """
        Initialize the ExamplesManager.

        Args:
            storage_dir: Directory to store example files
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._examples: Dict[str, CodeExample] = {}
        self._load_all_examples()

    def add_example(self, example: CodeExample) -> None:
        """
        Add a code example.

        Args:
            example: CodeExample to add
        """
        self._examples[example.id] = example
        self._save_example(example)

    def get_examples_by_module(self, module: str) -> List[CodeExample]:
        """
        Get all examples for a module.

        Args:
            module: Module name (errors, safe, learn, patterns, config, documentation)

        Returns:
            List of CodeExample objects for the module
        """
        return [ex for ex in self._examples.values() if ex.module == module]

    def get_example(self, id: str) -> Optional[CodeExample]:
        """
        Get a specific example by ID.

        Args:
            id: Example ID

        Returns:
            CodeExample if found, None otherwise
        """
        return self._examples.get(id)

    def list_all_examples(self) -> List[CodeExample]:
        """
        List all examples.

        Returns:
            List of all CodeExample objects
        """
        return list(self._examples.values())

    def validate_example(self, example: CodeExample) -> ValidationResult:
        """
        Validate a code example.

        Args:
            example: CodeExample to validate

        Returns:
            ValidationResult with validation status
        """
        errors = []
        warnings = []

        # Check required fields
        if not example.id:
            errors.append("Example must have an id")
        if not example.module:
            errors.append("Example must have a module")
        if not example.title:
            errors.append("Example must have a title")
        if not example.code:
            errors.append("Example must have code")
        if not example.explanation:
            errors.append("Example must have an explanation")

        # Validate module
        valid_modules = {"errors", "safe", "learn", "patterns", "config", "documentation"}
        if example.module and example.module not in valid_modules:
            errors.append(f"Invalid module: {example.module}. Must be one of {valid_modules}")

        # Validate difficulty
        valid_difficulties = {"beginner", "intermediate", "advanced"}
        if example.difficulty and example.difficulty not in valid_difficulties:
            errors.append(
                f"Invalid difficulty: {example.difficulty}. Must be one of {valid_difficulties}"
            )

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def _save_example(self, example: CodeExample) -> None:
        """
        Save an example to disk.

        Args:
            example: CodeExample to save
        """
        module_dir = self.storage_dir / example.module
        module_dir.mkdir(parents=True, exist_ok=True)

        example_file = module_dir / f"{example.id}.json"
        example_data = {
            "id": example.id,
            "module": example.module,
            "title": example.title,
            "code": example.code,
            "expected_output": example.expected_output,
            "explanation": example.explanation,
            "variations": example.variations,
            "difficulty": example.difficulty,
            "tags": example.tags,
        }

        with open(example_file, "w") as f:
            json.dump(example_data, f, indent=2)

    def _load_all_examples(self) -> None:
        """Load all examples from disk."""
        if not self.storage_dir.exists():
            return

        for module_dir in self.storage_dir.iterdir():
            if not module_dir.is_dir():
                continue

            for example_file in module_dir.glob("*.json"):
                try:
                    with open(example_file, "r") as f:
                        data = json.load(f)
                        example = CodeExample(
                            id=data["id"],
                            module=data["module"],
                            title=data["title"],
                            code=data["code"],
                            expected_output=data["expected_output"],
                            explanation=data["explanation"],
                            variations=data.get("variations", []),
                            difficulty=data.get("difficulty", "beginner"),
                            tags=data.get("tags", []),
                        )
                        self._examples[example.id] = example
                except Exception:
                    # Skip malformed files
                    pass
