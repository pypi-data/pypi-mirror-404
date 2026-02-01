"""
Main transformation script for README improvements.

This script orchestrates the complete README transformation process,
including backup creation, transformation, validation, and error handling.
"""

import sys
from pathlib import Path
from typing import Optional

from fishertools.readme_transformer import (
    ReadmeTransformer,
    FeatureEntry,
)


def transform_readme(
    readme_path: str = "README.md",
    create_backup: bool = True,
    features: Optional[list] = None,
    target_audience_bullets: Optional[list] = None,
) -> bool:
    """
    Transform the README file with improved structure.

    Args:
        readme_path: Path to the README.md file
        create_backup: Whether to create a backup before transformation
        features: List of feature entries (dicts with 'task' and 'function' keys)
        target_audience_bullets: Custom target audience bullet points

    Returns:
        True if transformation was successful, False otherwise

    Raises:
        FileNotFoundError: If README file does not exist
        IOError: If file operations fail
    """
    transformer = ReadmeTransformer(readme_path)

    # Validate README exists
    if not transformer.validate_readme_exists():
        raise FileNotFoundError(f"README file not found: {readme_path}")

    # Create backup if requested
    if create_backup:
        backup_path = transformer.create_backup()
        print(f"✓ Backup created: {backup_path}")

    # Convert feature dicts to FeatureEntry objects if provided
    feature_entries = None
    if features:
        feature_entries = [
            FeatureEntry(task=f["task"], function=f["function"]) for f in features
        ]

    # Transform the README
    try:
        transformed_content = transformer.transform(
            features=feature_entries,
            target_audience_bullets=target_audience_bullets,
        )
        print("✓ README transformation completed")
    except Exception as e:
        print(f"✗ Transformation failed: {e}", file=sys.stderr)
        return False

    # Validate the transformed content
    is_valid, error_message = transformer.validate_transformed_content(
        transformed_content
    )
    if not is_valid:
        print(f"✗ Validation failed: {error_message}", file=sys.stderr)
        return False
    print("✓ Content validation passed")

    # Write the transformed content
    try:
        transformer.write_transformed_readme(transformed_content)
        print(f"✓ README updated: {readme_path}")
    except IOError as e:
        print(f"✗ Failed to write README: {e}", file=sys.stderr)
        return False

    return True


def main() -> int:
    """
    Main entry point for the transformation script.

    Returns:
        0 if successful, 1 if failed
    """
    try:
        success = transform_readme()
        return 0 if success else 1
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
