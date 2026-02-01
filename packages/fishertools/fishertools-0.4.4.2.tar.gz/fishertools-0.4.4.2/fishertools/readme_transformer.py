"""
README transformation infrastructure for fishertools.

This module provides utilities for parsing, transforming, and validating
the README file structure while preserving existing content.
"""

import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple


@dataclass
class ReadmeSection:
    """Represents a section of the README document."""

    title: Optional[str]
    content: str
    level: int = 0  # Heading level (0 for no heading)


@dataclass
class FeatureEntry:
    """Represents a single feature entry in the feature table."""

    task: str  # Russian task description
    function: str  # Function to call


class ReadmeParser:
    """Parses and extracts sections from README markdown files."""

    def __init__(self, readme_path: str) -> None:
        """
        Initialize the parser with a README file path.

        Args:
            readme_path: Path to the README.md file
        """
        self.readme_path = Path(readme_path)
        self.content: str = ""
        self.sections: List[ReadmeSection] = []

    def read_file(self) -> str:
        """
        Read the README file content.

        Returns:
            The content of the README file

        Raises:
            FileNotFoundError: If the README file does not exist
            IOError: If the file cannot be read
        """
        if not self.readme_path.exists():
            raise FileNotFoundError(f"README file not found: {self.readme_path}")

        try:
            with open(self.readme_path, 'r', encoding='utf-8') as f:
                self.content = f.read()
            return self.content
        except IOError as e:
            raise IOError(f"Failed to read README file: {e}")

    def extract_first_sentence(self) -> str:
        """
        Extract the first introductory sentence from the README.

        Returns:
            The first sentence of the README content
        """
        lines = self.content.strip().split("\n")
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#"):
                # Extract just the first sentence (up to period, exclamation, or question mark)
                sentence = line.split(".")[0].split("!")[0].split("?")[0]
                if sentence.strip():
                    return sentence.strip()
        return ""

    def parse_sections(self) -> List[ReadmeSection]:
        """
        Parse README content into sections.

        Returns:
            List of ReadmeSection objects representing document structure
        """
        self.sections = []
        lines = self.content.split("\n")
        current_section = ReadmeSection(title=None, content="", level=0)

        for line in lines:
            if line.startswith("#"):
                # Save previous section if it has content
                if current_section.content.strip():
                    self.sections.append(current_section)

                # Create new section
                level = len(line) - len(line.lstrip("#"))
                title = line.lstrip("#").strip()
                current_section = ReadmeSection(
                    title=title, content="", level=level
                )
            else:
                current_section.content += line + "\n"

        # Add final section
        if current_section.content.strip():
            self.sections.append(current_section)

        return self.sections

    def extract_detailed_content(self) -> str:
        """
        Extract all content after the first introductory sentence.

        Returns:
            The detailed content sections of the README
        """
        lines = self.content.strip().split("\n")
        first_sentence_found = False
        detailed_lines = []

        for line in lines:
            if not first_sentence_found:
                line_stripped = line.strip()
                if line_stripped and not line_stripped.startswith("#"):
                    # Skip the first sentence line
                    first_sentence_found = True
                    continue
            detailed_lines.append(line)

        return "\n".join(detailed_lines).strip()

    def identify_feature_descriptions(self) -> List[Tuple[str, str]]:
        """
        Identify and extract feature descriptions from the README.

        Returns:
            List of tuples containing (feature_name, feature_description)
        """
        features = []
        lines = self.content.split("\n")

        for i, line in enumerate(lines):
            # Look for lines that might be feature descriptions
            if "explain_error" in line.lower() or "safe_read_file" in line.lower():
                # Extract the feature and its description
                feature_name = line.strip()
                description = ""

                # Collect following lines as description
                j = i + 1
                while j < len(lines) and lines[j].strip() and not lines[j].startswith("#"):
                    description += lines[j] + " "
                    j += 1

                if feature_name:
                    features.append((feature_name, description.strip()))

        return features

    def identify_introduction_boundary(self) -> int:
        """
        Identify the line number where the introduction ends.

        Returns:
            Line number where detailed content begins
        """
        lines = self.content.strip().split("\n")
        first_sentence_found = False

        for i, line in enumerate(lines):
            line_stripped = line.strip()

            # Skip empty lines at the beginning
            if not line_stripped:
                continue

            # Skip headings
            if line_stripped.startswith("#"):
                continue

            # First non-heading, non-empty line is the introduction
            if not first_sentence_found:
                first_sentence_found = True
                # Return the index after the introduction line
                return i + 1

        return 0

    def identify_feature_list_section(self) -> Optional[Tuple[int, int]]:
        """
        Identify the boundaries of any existing feature list section.

        Returns:
            Tuple of (start_line, end_line) for feature list, or None if not found
        """
        lines = self.content.split("\n")
        feature_section_start = None
        feature_section_end = None

        for i, line in enumerate(lines):
            # Look for feature-related keywords
            if any(
                keyword in line.lower()
                for keyword in [
                    "возможности",
                    "features",
                    "функции",
                    "capabilities",
                ]
            ):
                if line.startswith("#"):
                    feature_section_start = i
                    # Find the end of this section (next heading or end of file)
                    for j in range(i + 1, len(lines)):
                        if lines[j].startswith("#"):
                            feature_section_end = j
                            break
                    if feature_section_end is None:
                        feature_section_end = len(lines)
                    return (feature_section_start, feature_section_end)

        return None


class BackupManager:
    """Manages backup and recovery of README files."""

    def __init__(self, readme_path: str, backup_dir: str = ".readme_backups") -> None:
        """
        Initialize the backup manager.

        Args:
            readme_path: Path to the README.md file
            backup_dir: Directory to store backups
        """
        self.readme_path = Path(readme_path)
        self.backup_dir = Path(backup_dir)

    def create_backup(self) -> Path:
        """
        Create a timestamped backup of the README file.

        Returns:
            Path to the created backup file

        Raises:
            FileNotFoundError: If the README file does not exist
            IOError: If backup cannot be created
        """
        if not self.readme_path.exists():
            raise FileNotFoundError(f"README file not found: {self.readme_path}")

        # Create backup directory if it doesn't exist
        self.backup_dir.mkdir(exist_ok=True)

        # Generate timestamped backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"README_backup_{timestamp}.md"

        try:
            shutil.copy2(self.readme_path, backup_path)
            return backup_path
        except IOError as e:
            raise IOError(f"Failed to create backup: {e}")

    def list_backups(self) -> List[Path]:
        """
        List all available backup files.

        Returns:
            List of backup file paths, sorted by creation time (newest first)
        """
        if not self.backup_dir.exists():
            return []

        backups = sorted(
            self.backup_dir.glob("README_backup_*.md"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        return backups

    def restore_backup(self, backup_path: Path) -> None:
        """
        Restore README from a backup file.

        Args:
            backup_path: Path to the backup file to restore

        Raises:
            FileNotFoundError: If the backup file does not exist
            IOError: If restoration fails
        """
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")

        try:
            shutil.copy2(backup_path, self.readme_path)
        except IOError as e:
            raise IOError(f"Failed to restore backup: {e}")


class ReadmeStructure:
    """Defines and manages the structure of the transformed README."""

    def __init__(self) -> None:
        """Initialize the README structure."""
        self.introduction: str = ""
        self.installation_block: str = ""
        self.feature_table: str = ""
        self.target_audience: str = ""
        self.existing_content: str = ""

    def set_introduction(self, text: str) -> None:
        """Set the introduction section."""
        self.introduction = text

    def set_installation_block(self, command: str = "pip install fishertools") -> None:
        """
        Set the installation block.

        Args:
            command: The installation command to display
        """
        self.installation_block = f"```bash\n{command}\n```"

    def set_feature_table(self, features: Optional[List[FeatureEntry]] = None) -> None:
        """
        Set the feature table from a list of feature entries.

        Args:
            features: List of FeatureEntry objects. If None, uses default features.
        """
        if features is None:
            features = self._get_default_features()

        table_lines = ["| Задача | Что вызвать |", "|--------|-------------|"]

        for feature in features:
            table_lines.append(f"| {feature.task} | {feature.function} |")

        self.feature_table = "\n".join(table_lines)

    @staticmethod
    def _get_default_features() -> List[FeatureEntry]:
        """
        Get the default feature entries for the feature table.

        Returns:
            List of default FeatureEntry objects
        """
        return [
            FeatureEntry("Объяснить ошибку", "explain_error(e)"),
            FeatureEntry("Красиво показать traceback", "explain_error(e)"),
            FeatureEntry("Безопасно читать файл", "safe_read_file(path)"),
        ]

    def set_target_audience(
        self,
        title: str = "Для кого эта библиотека",
        bullets: Optional[List[str]] = None,
    ) -> None:
        """
        Set the target audience section.

        Args:
            title: Section title
            bullets: List of bullet points
        """
        if bullets is None:
            bullets = [
                "Ты только начал изучать Python",
                "Сообщения об ошибках кажутся страшными и непонятными",
                "Хочешь, чтобы ошибки объяснялись на нормальном русском с примерами",
            ]

        lines = [f"## {title}", ""]
        for bullet in bullets:
            lines.append(f"- {bullet}")

        self.target_audience = "\n".join(lines)

    def set_existing_content(self, content: str) -> None:
        """Set the existing detailed content."""
        self.existing_content = content

    def assemble(self) -> str:
        """
        Assemble all sections into the final README content.

        Returns:
            The complete transformed README content
        """
        sections = [
            self.introduction,
            "",
            self.installation_block,
            "",
            self.feature_table,
            "",
            self.target_audience,
            "",
            self.existing_content,
        ]

        # Filter out empty sections and join
        content = "\n".join(s for s in sections if s)
        return content


class MarkdownValidator:
    """Validates markdown syntax and structure."""

    @staticmethod
    def validate_markdown_syntax(content: str) -> Tuple[bool, Optional[str]]:
        """
        Validate basic markdown syntax.

        Args:
            content: The markdown content to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        lines = content.split("\n")
        code_block_open = False
        code_block_marker = None

        for i, line in enumerate(lines, 1):
            # Check for code block markers
            if line.strip().startswith("```"):
                if not code_block_open:
                    code_block_open = True
                    code_block_marker = line.strip()
                else:
                    code_block_open = False

            # Check for unmatched brackets in links
            if "[" in line and "]" not in line:
                # This is a simple check; more complex validation could be added
                pass

        if code_block_open:
            return False, "Unclosed code block detected"

        return True, None

    @staticmethod
    def validate_document_structure(content: str) -> Tuple[bool, Optional[str]]:
        """
        Validate document structure ordering.

        Args:
            content: The markdown content to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        lines = content.split("\n")

        # Find key sections
        intro_idx = None
        install_idx = None
        feature_table_idx = None
        target_audience_idx = None

        for i, line in enumerate(lines):
            if intro_idx is None and line.strip() and not line.startswith("#"):
                intro_idx = i
            if "```bash" in line and install_idx is None:
                install_idx = i
            if "Задача" in line and "Что вызвать" in line and feature_table_idx is None:
                feature_table_idx = i
            if "Для кого эта библиотека" in line and target_audience_idx is None:
                target_audience_idx = i

        # Validate ordering
        indices = [
            (intro_idx, "introduction"),
            (install_idx, "installation block"),
            (feature_table_idx, "feature table"),
            (target_audience_idx, "target audience"),
        ]

        valid_indices = [(idx, name) for idx, name in indices if idx is not None]

        for i in range(len(valid_indices) - 1):
            if valid_indices[i][0] > valid_indices[i + 1][0]:
                return (
                    False,
                    f"Section ordering error: {valid_indices[i][1]} appears after {valid_indices[i + 1][1]}",
                )

        return True, None


class ReadmeTransformer:
    """Main transformer class that orchestrates README transformation."""

    def __init__(self, readme_path: str) -> None:
        """
        Initialize the transformer.

        Args:
            readme_path: Path to the README.md file
        """
        self.readme_path = readme_path
        self.parser = ReadmeParser(readme_path)
        self.backup_manager = BackupManager(readme_path)
        self.structure = ReadmeStructure()
        self.validator = MarkdownValidator()

    def validate_readme_exists(self) -> bool:
        """
        Validate that the README file exists.

        Returns:
            True if README exists, False otherwise
        """
        return Path(self.readme_path).exists()

    def parse_readme(self) -> None:
        """Parse the README file and extract sections."""
        self.parser.read_file()
        self.parser.parse_sections()

    def extract_content(self) -> Tuple[str, str]:
        """
        Extract introduction and existing content from README.

        Returns:
            Tuple of (introduction, existing_content)
        """
        # Ensure parser has read the file
        if not self.parser.content:
            self.parser.read_file()

        introduction = self.parser.extract_first_sentence()
        existing_content = self.parser.content

        return introduction, existing_content

    def create_backup(self) -> Path:
        """
        Create a backup of the original README.

        Returns:
            Path to the created backup file
        """
        return self.backup_manager.create_backup()

    def transform(
        self,
        features: Optional[List[FeatureEntry]] = None,
        target_audience_bullets: Optional[List[str]] = None,
    ) -> str:
        """
        Transform the README with new structure.

        Args:
            features: List of features for the feature table. If None, uses default features.
            target_audience_bullets: Custom target audience bullet points

        Returns:
            The transformed README content
        """
        # Parse the original README
        self.parse_readme()

        # Extract content
        introduction, existing_content = self.extract_content()

        # Set up structure
        self.structure.set_introduction(introduction)
        self.structure.set_installation_block()

        # Set feature table (uses default if not provided)
        self.structure.set_feature_table(features)

        # Set target audience
        self.structure.set_target_audience(bullets=target_audience_bullets)

        # Set existing content
        self.structure.set_existing_content(existing_content)

        # Assemble and return
        return self.structure.assemble()

    def write_transformed_readme(self, content: str) -> None:
        """
        Write the transformed content to the README file.

        Args:
            content: The transformed README content

        Raises:
            IOError: If writing fails
        """
        try:
            with open(self.readme_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except IOError as e:
            raise IOError(f"Failed to write transformed README: {e}")

    def validate_transformed_content(self, content: str) -> Tuple[bool, Optional[str]]:
        """
        Validate the transformed README content.

        Args:
            content: The transformed README content to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate markdown syntax
        syntax_valid, syntax_error = self.validator.validate_markdown_syntax(content)
        if not syntax_valid:
            return False, syntax_error

        # Validate document structure
        structure_valid, structure_error = self.validator.validate_document_structure(
            content
        )
        if not structure_valid:
            return False, structure_error

        return True, None
