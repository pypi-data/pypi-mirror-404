"""
Tests for README transformation infrastructure.

Tests the core components: ReadmeParser, BackupManager, ReadmeStructure,
and ReadmeTransformer.
"""

import tempfile
from pathlib import Path
from typing import List

import pytest

from fishertools.readme_transformer import (
    BackupManager,
    FeatureEntry,
    ReadmeParser,
    ReadmeSection,
    ReadmeStructure,
    ReadmeTransformer,
)


class TestReadmeParser:
    """Tests for ReadmeParser class."""

    def test_read_file_success(self, tmp_path: Path) -> None:
        """Test successful reading of README file."""
        readme_path = tmp_path / "README.md"
        test_content = "# Test README\n\nThis is a test."
        readme_path.write_text(test_content, encoding="utf-8")

        parser = ReadmeParser(str(readme_path))
        content = parser.read_file()

        assert content == test_content

    def test_read_file_not_found(self, tmp_path: Path) -> None:
        """Test error when README file does not exist."""
        readme_path = tmp_path / "nonexistent.md"

        parser = ReadmeParser(str(readme_path))

        with pytest.raises(FileNotFoundError):
            parser.read_file()

    def test_extract_first_sentence(self, tmp_path: Path) -> None:
        """Test extraction of first introductory sentence."""
        readme_path = tmp_path / "README.md"
        test_content = "First sentence here\n\n# Heading\n\nMore content"
        readme_path.write_text(test_content, encoding="utf-8")

        parser = ReadmeParser(str(readme_path))
        parser.read_file()
        first_sentence = parser.extract_first_sentence()

        assert first_sentence == "First sentence here"

    def test_extract_first_sentence_with_heading(self, tmp_path: Path) -> None:
        """Test extraction skips headings to find first sentence."""
        readme_path = tmp_path / "README.md"
        test_content = "# Title\n\nFirst real sentence\n\nMore content"
        readme_path.write_text(test_content, encoding="utf-8")

        parser = ReadmeParser(str(readme_path))
        parser.read_file()
        first_sentence = parser.extract_first_sentence()

        assert first_sentence == "First real sentence"

    def test_parse_sections(self, tmp_path: Path) -> None:
        """Test parsing of README sections."""
        readme_path = tmp_path / "README.md"
        test_content = "# Heading 1\n\nContent 1\n\n## Heading 2\n\nContent 2"
        readme_path.write_text(test_content, encoding="utf-8")

        parser = ReadmeParser(str(readme_path))
        parser.read_file()
        sections = parser.parse_sections()

        assert len(sections) >= 2
        assert any(s.title == "Heading 1" for s in sections)
        assert any(s.title == "Heading 2" for s in sections)

    def test_parse_sections_preserves_content(self, tmp_path: Path) -> None:
        """Test that parsing preserves section content."""
        readme_path = tmp_path / "README.md"
        test_content = "# Section\n\nThis is content\nWith multiple lines"
        readme_path.write_text(test_content, encoding="utf-8")

        parser = ReadmeParser(str(readme_path))
        parser.read_file()
        sections = parser.parse_sections()

        assert any("This is content" in s.content for s in sections)

    def test_extract_detailed_content(self, tmp_path: Path) -> None:
        """Test extraction of detailed content after introduction."""
        readme_path = tmp_path / "README.md"
        test_content = "Introduction line\n\n# Section\n\nDetailed content here"
        readme_path.write_text(test_content, encoding="utf-8")

        parser = ReadmeParser(str(readme_path))
        parser.read_file()
        detailed = parser.extract_detailed_content()

        assert "Detailed content here" in detailed
        assert "Introduction line" not in detailed or detailed.count("Introduction") == 0

    def test_identify_introduction_boundary(self, tmp_path: Path) -> None:
        """Test identification of introduction boundary."""
        readme_path = tmp_path / "README.md"
        test_content = "First intro\n\n# Heading\n\nContent"
        readme_path.write_text(test_content, encoding="utf-8")

        parser = ReadmeParser(str(readme_path))
        parser.read_file()
        boundary = parser.identify_introduction_boundary()

        assert boundary > 0

    def test_identify_feature_list_section(self, tmp_path: Path) -> None:
        """Test identification of feature list section."""
        readme_path = tmp_path / "README.md"
        test_content = "Intro\n\n## Основные возможности\n\nFeature 1\nFeature 2\n\n## Other"
        readme_path.write_text(test_content, encoding="utf-8")

        parser = ReadmeParser(str(readme_path))
        parser.read_file()
        feature_section = parser.identify_feature_list_section()

        assert feature_section is not None
        assert feature_section[0] >= 0
        assert feature_section[1] > feature_section[0]


class TestBackupManager:
    """Tests for BackupManager class."""

    def test_create_backup_success(self, tmp_path: Path) -> None:
        """Test successful backup creation."""
        readme_path = tmp_path / "README.md"
        readme_path.write_text("Test content", encoding="utf-8")

        backup_manager = BackupManager(str(readme_path), str(tmp_path / "backups"))
        backup_path = backup_manager.create_backup()

        assert backup_path.exists()
        assert backup_path.read_text(encoding="utf-8") == "Test content"

    def test_create_backup_file_not_found(self, tmp_path: Path) -> None:
        """Test error when README file does not exist."""
        readme_path = tmp_path / "nonexistent.md"

        backup_manager = BackupManager(str(readme_path), str(tmp_path / "backups"))

        with pytest.raises(FileNotFoundError):
            backup_manager.create_backup()

    def test_list_backups(self, tmp_path: Path) -> None:
        """Test listing of backup files."""
        import time

        readme_path = tmp_path / "README.md"
        readme_path.write_text("Test content", encoding="utf-8")

        backup_manager = BackupManager(str(readme_path), str(tmp_path / "backups"))

        # Create multiple backups with delay to ensure different timestamps
        backup_manager.create_backup()
        time.sleep(1.1)  # Sleep to ensure different timestamp
        backup_manager.create_backup()

        backups = backup_manager.list_backups()

        assert len(backups) >= 2

    def test_restore_backup(self, tmp_path: Path) -> None:
        """Test restoration from backup."""
        readme_path = tmp_path / "README.md"
        original_content = "Original content"
        readme_path.write_text(original_content, encoding="utf-8")

        backup_manager = BackupManager(str(readme_path), str(tmp_path / "backups"))
        backup_path = backup_manager.create_backup()

        # Modify the README
        readme_path.write_text("Modified content", encoding="utf-8")

        # Restore from backup
        backup_manager.restore_backup(backup_path)

        assert readme_path.read_text(encoding="utf-8") == original_content

    def test_restore_backup_not_found(self, tmp_path: Path) -> None:
        """Test error when backup file does not exist."""
        readme_path = tmp_path / "README.md"
        readme_path.write_text("Test content", encoding="utf-8")

        backup_manager = BackupManager(str(readme_path), str(tmp_path / "backups"))
        nonexistent_backup = tmp_path / "backups" / "nonexistent.md"

        with pytest.raises(FileNotFoundError):
            backup_manager.restore_backup(nonexistent_backup)


class TestReadmeStructure:
    """Tests for ReadmeStructure class."""

    def test_set_introduction(self) -> None:
        """Test setting introduction section."""
        structure = ReadmeStructure()
        intro = "This is the introduction"

        structure.set_introduction(intro)

        assert structure.introduction == intro

    def test_set_installation_block_default(self) -> None:
        """Test setting installation block with default command."""
        structure = ReadmeStructure()

        structure.set_installation_block()

        assert "pip install fishertools" in structure.installation_block
        assert structure.installation_block.startswith("```bash")
        assert structure.installation_block.endswith("```")

    def test_set_installation_block_custom(self) -> None:
        """Test setting installation block with custom command."""
        structure = ReadmeStructure()
        custom_command = "pip install custom-package"

        structure.set_installation_block(custom_command)

        assert custom_command in structure.installation_block

    def test_set_feature_table(self) -> None:
        """Test setting feature table."""
        structure = ReadmeStructure()
        features = [
            FeatureEntry("Объяснить ошибку", "explain_error(e)"),
            FeatureEntry("Безопасно читать файл", "safe_read_file(path)"),
        ]

        structure.set_feature_table(features)

        assert "Задача" in structure.feature_table
        assert "Что вызвать" in structure.feature_table
        assert "explain_error(e)" in structure.feature_table
        assert "safe_read_file(path)" in structure.feature_table

    def test_set_feature_table_format(self) -> None:
        """Test that feature table uses proper markdown format."""
        structure = ReadmeStructure()
        features = [FeatureEntry("Task", "function()")]

        structure.set_feature_table(features)

        lines = structure.feature_table.split("\n")
        assert lines[0].startswith("|")
        assert lines[1].startswith("|")

    def test_set_target_audience_default(self) -> None:
        """Test setting target audience with default bullets."""
        structure = ReadmeStructure()

        structure.set_target_audience()

        assert "Для кого эта библиотека" in structure.target_audience
        assert "Ты только начал изучать Python" in structure.target_audience
        assert "Сообщения об ошибках" in structure.target_audience
        assert "нормальном русском" in structure.target_audience

    def test_set_target_audience_custom(self) -> None:
        """Test setting target audience with custom bullets."""
        structure = ReadmeStructure()
        custom_bullets = ["Bullet 1", "Bullet 2", "Bullet 3"]

        structure.set_target_audience(bullets=custom_bullets)

        for bullet in custom_bullets:
            assert bullet in structure.target_audience

    def test_set_existing_content(self) -> None:
        """Test setting existing content."""
        structure = ReadmeStructure()
        content = "## Existing Section\n\nThis is existing content"

        structure.set_existing_content(content)

        assert structure.existing_content == content

    def test_assemble_structure(self) -> None:
        """Test assembling all sections into final content."""
        structure = ReadmeStructure()
        structure.set_introduction("Introduction")
        structure.set_installation_block()
        structure.set_feature_table([FeatureEntry("Task", "func()")])
        structure.set_target_audience()
        structure.set_existing_content("Existing content")

        assembled = structure.assemble()

        assert "Introduction" in assembled
        assert "pip install fishertools" in assembled
        assert "Task" in assembled
        assert "Для кого эта библиотека" in assembled
        assert "Existing content" in assembled


class TestReadmeTransformer:
    """Tests for ReadmeTransformer class."""

    def test_validate_readme_exists(self, tmp_path: Path) -> None:
        """Test validation of README existence."""
        readme_path = tmp_path / "README.md"
        readme_path.write_text("Test", encoding="utf-8")

        transformer = ReadmeTransformer(str(readme_path))

        assert transformer.validate_readme_exists() is True

    def test_validate_readme_not_exists(self, tmp_path: Path) -> None:
        """Test validation when README does not exist."""
        readme_path = tmp_path / "nonexistent.md"

        transformer = ReadmeTransformer(str(readme_path))

        assert transformer.validate_readme_exists() is False

    def test_parse_readme(self, tmp_path: Path) -> None:
        """Test parsing README file."""
        readme_path = tmp_path / "README.md"
        test_content = "# Title\n\nContent here"
        readme_path.write_text(test_content, encoding="utf-8")

        transformer = ReadmeTransformer(str(readme_path))
        transformer.parse_readme()

        assert transformer.parser.content == test_content

    def test_extract_content(self, tmp_path: Path) -> None:
        """Test extraction of introduction and existing content."""
        readme_path = tmp_path / "README.md"
        test_content = "First sentence\n\n# Heading\n\nMore content"
        readme_path.write_text(test_content, encoding="utf-8")

        transformer = ReadmeTransformer(str(readme_path))
        introduction, existing = transformer.extract_content()

        assert "First sentence" in introduction
        assert "More content" in existing

    def test_create_backup(self, tmp_path: Path) -> None:
        """Test backup creation."""
        readme_path = tmp_path / "README.md"
        readme_path.write_text("Test content", encoding="utf-8")

        transformer = ReadmeTransformer(str(readme_path))
        backup_path = transformer.create_backup()

        assert backup_path.exists()

    def test_transform_basic(self, tmp_path: Path) -> None:
        """Test basic README transformation."""
        readme_path = tmp_path / "README.md"
        test_content = "Introduction\n\n# Section\n\nContent"
        readme_path.write_text(test_content, encoding="utf-8")

        transformer = ReadmeTransformer(str(readme_path))
        transformed = transformer.transform()

        assert "Introduction" in transformed
        assert "pip install fishertools" in transformed
        assert "Для кого эта библиотека" in transformed

    def test_transform_with_features(self, tmp_path: Path) -> None:
        """Test transformation with custom features."""
        readme_path = tmp_path / "README.md"
        readme_path.write_text("Introduction\n\nContent", encoding="utf-8")

        features = [
            FeatureEntry("Feature 1", "func1()"),
            FeatureEntry("Feature 2", "func2()"),
        ]

        transformer = ReadmeTransformer(str(readme_path))
        transformed = transformer.transform(features=features)

        assert "Feature 1" in transformed
        assert "func1()" in transformed
        assert "Feature 2" in transformed
        assert "func2()" in transformed

    def test_write_transformed_readme(self, tmp_path: Path) -> None:
        """Test writing transformed README to file."""
        readme_path = tmp_path / "README.md"
        readme_path.write_text("Original", encoding="utf-8")

        transformer = ReadmeTransformer(str(readme_path))
        new_content = "Transformed content"
        transformer.write_transformed_readme(new_content)

        assert readme_path.read_text(encoding="utf-8") == new_content

    def test_full_transformation_workflow(self, tmp_path: Path) -> None:
        """Test complete transformation workflow."""
        readme_path = tmp_path / "README.md"
        original_content = "Original Introduction\n\n# Section\n\nOriginal content"
        readme_path.write_text(original_content, encoding="utf-8")

        transformer = ReadmeTransformer(str(readme_path))

        # Create backup
        backup_path = transformer.create_backup()
        assert backup_path.exists()

        # Transform
        features = [FeatureEntry("Task", "function()")]
        transformed = transformer.transform(features=features)

        # Write
        transformer.write_transformed_readme(transformed)

        # Verify
        result = readme_path.read_text(encoding="utf-8")
        assert "pip install fishertools" in result
        assert "Для кого эта библиотека" in result
        assert "Task" in result


# Property-based tests using hypothesis
from hypothesis import given, strategies as st, settings, HealthCheck
import tempfile


class TestReadmeContentPreservation:
    """Property-based tests for content preservation."""

    @given(
        intro=st.text(
            min_size=1,
            max_size=100,
            alphabet=st.characters(
                blacklist_categories=("Cc", "Cs"),
                blacklist_characters="\x00\r",
            ),
        ),
        content=st.text(
            min_size=1,
            max_size=500,
            alphabet=st.characters(
                blacklist_categories=("Cc", "Cs"),
                blacklist_characters="\x00\r",
            ),
        ),
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_content_preservation(self, intro: str, content: str) -> None:
        """
        Property 5: Content Preservation

        **Validates: Requirements 4.1, 4.3**

        For any README transformation, the original introductory sentence
        should remain as the first content and all existing detailed
        documentation should be preserved without loss.
        """
        # Skip if intro or content are empty after stripping
        if not intro.strip() or not content.strip():
            return

        with tempfile.TemporaryDirectory() as tmp_dir:
            readme_path = Path(tmp_dir) / "README.md"
            test_content = f"{intro}\n\n# Section\n\n{content}"
            readme_path.write_text(test_content, encoding="utf-8")

            transformer = ReadmeTransformer(str(readme_path))
            transformed = transformer.transform()

            # Verify that the introduction is preserved (or its first sentence)
            intro_stripped = intro.strip()
            first_sentence = intro_stripped.split(".")[0].split("!")[0].split("?")[0].strip()
            
            assert (
                intro_stripped in transformed
                or first_sentence in transformed
            ), f"Introduction '{intro_stripped}' not found in transformed content"

            # Verify that the existing content is preserved
            content_stripped = content.strip()
            assert (
                content_stripped in transformed
            ), f"Content '{content_stripped}' not found in transformed content"


class TestInstallationBlockProperty:
    """Property-based tests for installation block."""

    @given(
        intro=st.text(
            min_size=1,
            max_size=100,
            alphabet=st.characters(
                blacklist_categories=("Cc", "Cs"),
                blacklist_characters="\x00\r",
            ),
        ),
        content=st.text(
            min_size=1,
            max_size=500,
            alphabet=st.characters(
                blacklist_categories=("Cc", "Cs"),
                blacklist_characters="\x00\r",
            ),
        ),
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_installation_block_content_and_format(
        self, intro: str, content: str
    ) -> None:
        """
        Property 2: Installation Block Content and Format

        **Validates: Requirements 1.2, 1.3**

        For any README file, the installation block should contain exactly
        "pip install fishertools" and be formatted as a proper markdown code block.
        """
        # Skip if intro or content are empty after stripping
        if not intro.strip() or not content.strip():
            return

        with tempfile.TemporaryDirectory() as tmp_dir:
            readme_path = Path(tmp_dir) / "README.md"
            test_content = f"{intro}\n\n# Section\n\n{content}"
            readme_path.write_text(test_content, encoding="utf-8")

            transformer = ReadmeTransformer(str(readme_path))
            transformed = transformer.transform()

            # Verify installation block contains the exact command
            assert (
                "pip install fishertools" in transformed
            ), "Installation command not found in transformed content"

            # Verify it's formatted as a code block
            assert (
                "```bash" in transformed
            ), "Installation block not formatted as bash code block"
            assert (
                "```" in transformed
            ), "Installation block missing closing code block marker"

            # Verify the code block structure
            lines = transformed.split("\n")
            bash_block_start = None
            bash_block_end = None

            for i, line in enumerate(lines):
                if line.strip() == "```bash":
                    bash_block_start = i
                elif bash_block_start is not None and line.strip() == "```":
                    bash_block_end = i
                    break

            assert (
                bash_block_start is not None
            ), "Opening bash code block marker not found"
            assert (
                bash_block_end is not None
            ), "Closing code block marker not found"
            assert (
                bash_block_end > bash_block_start
            ), "Code block end before start"

            # Verify the command is between the markers
            command_found = False
            for i in range(bash_block_start + 1, bash_block_end):
                if "pip install fishertools" in lines[i]:
                    command_found = True
                    break

            assert (
                command_found
            ), "Installation command not found between code block markers"


class TestFeatureTableProperty:
    """Property-based tests for feature table."""

    @given(
        intro=st.text(
            min_size=1,
            max_size=100,
            alphabet=st.characters(
                blacklist_categories=("Cc", "Cs"),
                blacklist_characters="\x00\r|",
            ),
        ),
        content=st.text(
            min_size=1,
            max_size=500,
            alphabet=st.characters(
                blacklist_categories=("Cc", "Cs"),
                blacklist_characters="\x00\r|",
            ),
        ),
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_feature_table_structure_and_content(
        self, intro: str, content: str
    ) -> None:
        """
        Property 3: Feature Table Structure and Content

        **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**

        For any README transformation, the feature table should have columns
        "Задача" and "Что вызвать", use proper markdown table format, and
        contain entries for "explain_error(e)" and "safe_read_file(path)".
        """
        # Skip if intro or content are empty after stripping
        if not intro.strip() or not content.strip():
            return

        with tempfile.TemporaryDirectory() as tmp_dir:
            readme_path = Path(tmp_dir) / "README.md"
            test_content = f"{intro}\n\n# Section\n\n{content}"
            readme_path.write_text(test_content, encoding="utf-8")

            transformer = ReadmeTransformer(str(readme_path))
            transformed = transformer.transform()

            # Verify table headers are present
            assert (
                "Задача" in transformed
            ), "Feature table header 'Задача' not found"
            assert (
                "Что вызвать" in transformed
            ), "Feature table header 'Что вызвать' not found"

            # Verify markdown table format (pipe characters)
            lines = transformed.split("\n")
            
            # Find table lines - they should have both headers and separator
            header_line_idx = None
            separator_line_idx = None
            
            for i, line in enumerate(lines):
                if "Задача" in line and "Что вызвать" in line:
                    header_line_idx = i
                elif header_line_idx is not None and "-----" in line:
                    separator_line_idx = i
                    break
            
            assert (
                header_line_idx is not None
            ), "Feature table header line not found"
            assert (
                separator_line_idx is not None
            ), "Feature table separator line not found"
            assert (
                separator_line_idx > header_line_idx
            ), "Separator line should come after header line"

            # Verify required function entries
            assert (
                "explain_error(e)" in transformed
            ), "Feature table missing 'explain_error(e)' entry"
            assert (
                "safe_read_file(path)" in transformed
            ), "Feature table missing 'safe_read_file(path)' entry"

            # Verify table structure: header and separator should have pipes
            header_line = lines[header_line_idx]
            separator_line = lines[separator_line_idx]
            
            assert (
                header_line.count("|") >= 2
            ), f"Header line does not have proper structure: {header_line}"
            assert (
                separator_line.count("|") >= 2
            ), f"Separator line does not have proper structure: {separator_line}"


class TestTargetAudienceSectionProperty:
    """Property-based tests for target audience section."""

    @given(
        intro=st.text(
            min_size=1,
            max_size=100,
            alphabet=st.characters(
                blacklist_categories=("Cc", "Cs"),
                blacklist_characters="\x00\r",
            ),
        ),
        content=st.text(
            min_size=1,
            max_size=500,
            alphabet=st.characters(
                blacklist_categories=("Cc", "Cs"),
                blacklist_characters="\x00\r",
            ),
        ),
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_target_audience_section_content(
        self, intro: str, content: str
    ) -> None:
        """
        Property 4: Target Audience Section Content

        **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

        For any README transformation, the target audience section should have
        the title "Для кого эта библиотека", contain exactly 3 bullet points,
        and include all three specified user descriptions.
        """
        # Skip if intro or content are empty after stripping
        if not intro.strip() or not content.strip():
            return

        with tempfile.TemporaryDirectory() as tmp_dir:
            readme_path = Path(tmp_dir) / "README.md"
            test_content = f"{intro}\n\n# Section\n\n{content}"
            readme_path.write_text(test_content, encoding="utf-8")

            transformer = ReadmeTransformer(str(readme_path))
            transformed = transformer.transform()

            # Verify section title is present
            assert (
                "Для кого эта библиотека" in transformed
            ), "Target audience section title not found"

            # Verify section title is formatted as a heading
            lines = transformed.split("\n")
            title_found = False
            for line in lines:
                if "Для кого эта библиотека" in line and line.startswith("##"):
                    title_found = True
                    break

            assert (
                title_found
            ), "Target audience section title not formatted as heading"

            # Verify all three required bullet points are present
            required_bullets = [
                "Ты только начал изучать Python",
                "Сообщения об ошибках кажутся страшными и непонятными",
                "Хочешь, чтобы ошибки объяснялись на нормальном русском с примерами",
            ]

            for bullet in required_bullets:
                assert (
                    bullet in transformed
                ), f"Required bullet point '{bullet}' not found in target audience section"

            # Verify exactly 3 bullet points in the section
            # Find the target audience section
            section_start = None
            section_end = None

            for i, line in enumerate(lines):
                if "Для кого эта библиотека" in line:
                    section_start = i
                elif section_start is not None and line.startswith("#") and i > section_start:
                    section_end = i
                    break

            if section_end is None:
                section_end = len(lines)

            # Count bullet points in the section
            bullet_count = 0
            for i in range(section_start, section_end):
                if lines[i].strip().startswith("- "):
                    bullet_count += 1

            assert (
                bullet_count == 3
            ), f"Expected exactly 3 bullet points, found {bullet_count}"

            # Verify bullet points are formatted correctly (start with "- ")
            for i in range(section_start, section_end):
                if any(bullet in lines[i] for bullet in required_bullets):
                    assert (
                        lines[i].strip().startswith("- ")
                    ), f"Bullet point not properly formatted: {lines[i]}"



class TestDocumentStructureOrderingProperty:
    """Property-based tests for document structure ordering."""

    @given(
        intro=st.text(
            min_size=10,
            max_size=100,
            alphabet=st.characters(
                blacklist_categories=("Cc", "Cs"),
                blacklist_characters="\x00\r#.",
            ),
        ),
        content=st.text(
            min_size=10,
            max_size=500,
            alphabet=st.characters(
                blacklist_categories=("Cc", "Cs"),
                blacklist_characters="\x00\r",
            ),
        ),
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_document_structure_ordering(
        self, intro: str, content: str
    ) -> None:
        """
        Property 1: Document Structure Ordering

        **Validates: Requirements 1.1, 1.4, 2.6, 3.6, 4.2**

        For any valid README transformation, the document sections should appear
        in this exact order: introduction, installation block, feature table,
        target audience section, then existing detailed content.
        """
        # Skip if intro or content are empty after stripping
        if not intro.strip() or not content.strip():
            return

        with tempfile.TemporaryDirectory() as tmp_dir:
            readme_path = Path(tmp_dir) / "README.md"
            # Ensure intro ends with a period to form a valid sentence
            intro_with_period = intro.strip() + "." if not intro.strip().endswith((".","!","?")) else intro.strip()
            test_content = f"{intro_with_period}\n\n# Section\n\n{content}"
            readme_path.write_text(test_content, encoding="utf-8")

            transformer = ReadmeTransformer(str(readme_path))
            transformed = transformer.transform()

            lines = transformed.split("\n")

            # Find indices of key sections
            intro_idx = None
            install_idx = None
            feature_table_idx = None
            target_audience_idx = None
            existing_content_idx = None

            for i, line in enumerate(lines):
                # Introduction is the first non-empty, non-heading line
                if intro_idx is None and line.strip() and not line.startswith("#"):
                    intro_idx = i

                # Installation block starts with ```bash
                if install_idx is None and "```bash" in line:
                    install_idx = i

                # Feature table has both headers
                if (
                    feature_table_idx is None
                    and "Задача" in line
                    and "Что вызвать" in line
                ):
                    feature_table_idx = i

                # Target audience section
                if (
                    target_audience_idx is None
                    and "Для кого эта библиотека" in line
                ):
                    target_audience_idx = i

                # Existing content appears after target audience
                if (
                    existing_content_idx is None
                    and target_audience_idx is not None
                    and i > target_audience_idx
                    and line.strip()
                    and not line.startswith("#")
                    and "Для кого" not in line
                    and "Ты только" not in line
                    and "Сообщения" not in line
                    and "Хочешь" not in line
                ):
                    existing_content_idx = i

            # Verify all sections are present
            assert intro_idx is not None, "Introduction section not found"
            assert install_idx is not None, "Installation block not found"
            assert feature_table_idx is not None, "Feature table not found"
            assert target_audience_idx is not None, "Target audience section not found"

            # Verify ordering: introduction < installation < feature table < target audience
            assert (
                intro_idx < install_idx
            ), f"Introduction ({intro_idx}) should come before installation block ({install_idx})"

            assert (
                install_idx < feature_table_idx
            ), f"Installation block ({install_idx}) should come before feature table ({feature_table_idx})"

            assert (
                feature_table_idx < target_audience_idx
            ), f"Feature table ({feature_table_idx}) should come before target audience ({target_audience_idx})"

            # Verify markdown syntax is valid
            is_valid, error_msg = transformer.validate_transformed_content(transformed)
            assert (
                is_valid
            ), f"Transformed content has invalid markdown syntax: {error_msg}"



class TestLanguageConsistencyProperty:
    """Property-based tests for language consistency."""

    @given(
        intro=st.text(
            min_size=1,
            max_size=100,
            alphabet=st.characters(
                blacklist_categories=("Cc", "Cs"),
                blacklist_characters="\x00\r",
            ),
        ),
        content=st.text(
            min_size=1,
            max_size=500,
            alphabet=st.characters(
                blacklist_categories=("Cc", "Cs"),
                blacklist_characters="\x00\r",
            ),
        ),
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_language_consistency(self, intro: str, content: str) -> None:
        """
        Property 6: Language Consistency

        **Validates: Requirements 4.4**

        For any new content added to the README, it should use Russian language
        to match the existing documentation style.
        """
        # Skip if intro or content are empty after stripping
        if not intro.strip() or not content.strip():
            return

        with tempfile.TemporaryDirectory() as tmp_dir:
            readme_path = Path(tmp_dir) / "README.md"
            test_content = f"{intro}\n\n# Section\n\n{content}"
            readme_path.write_text(test_content, encoding="utf-8")

            transformer = ReadmeTransformer(str(readme_path))
            transformed = transformer.transform()

            # Define Russian language markers that should be present in new content
            russian_markers = [
                "Задача",  # Feature table header
                "Что вызвать",  # Feature table header
                "Для кого эта библиотека",  # Target audience section title
                "Ты только начал изучать Python",  # Target audience bullet 1
                "Сообщения об ошибках",  # Target audience bullet 2
                "нормальном русском",  # Target audience bullet 3
            ]

            # Verify all Russian language markers are present
            for marker in russian_markers:
                assert (
                    marker in transformed
                ), f"Russian language marker '{marker}' not found in transformed content"

            # Verify the installation block uses English (as it's a standard command)
            assert (
                "pip install fishertools" in transformed
            ), "Installation command not found"

            # Verify feature table entries use English function names
            assert (
                "explain_error(e)" in transformed
            ), "Function name 'explain_error(e)' not found"
            assert (
                "safe_read_file(path)" in transformed
            ), "Function name 'safe_read_file(path)' not found"

            # Verify that new sections (not from original content) use Russian
            lines = transformed.split("\n")

            # Find the target audience section
            target_audience_start = None
            for i, line in enumerate(lines):
                if "Для кого эта библиотека" in line:
                    target_audience_start = i
                    break

            assert (
                target_audience_start is not None
            ), "Target audience section not found"

            # Verify the section heading is in Russian
            assert (
                lines[target_audience_start].startswith("##")
            ), "Target audience should be a level 2 heading"

            # Verify feature table headers are in Russian
            feature_table_found = False
            for i, line in enumerate(lines):
                if "Задача" in line and "Что вызвать" in line:
                    feature_table_found = True
                    # Verify it's a proper table header
                    assert (
                        "|" in line
                    ), "Feature table header should use pipe characters"
                    break

            assert (
                feature_table_found
            ), "Feature table with Russian headers not found"
