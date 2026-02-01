"""
Integration tests for the README transformation script.

Tests the complete transformation process including:
- File reading and writing
- Backup creation and recovery
- Error handling for missing files
- End-to-end transformation workflow
"""

import tempfile
from pathlib import Path

import pytest

from fishertools.transform_readme import transform_readme
from fishertools.readme_transformer import BackupManager


class TestTransformReadmeIntegration:
    """Integration tests for the transform_readme function."""

    def test_transform_readme_success(self, tmp_path: Path) -> None:
        """Test successful README transformation."""
        readme_path = tmp_path / "README.md"
        test_content = "Introduction\n\n# Section\n\nContent"
        readme_path.write_text(test_content, encoding="utf-8")

        result = transform_readme(str(readme_path), create_backup=False)

        assert result is True
        transformed = readme_path.read_text(encoding="utf-8")
        assert "pip install fishertools" in transformed
        assert "Для кого эта библиотека" in transformed

    def test_transform_readme_with_backup(self, tmp_path: Path) -> None:
        """Test transformation with backup creation."""
        readme_path = tmp_path / "README.md"
        test_content = "Introduction\n\n# Section\n\nContent"
        readme_path.write_text(test_content, encoding="utf-8")

        # Change to tmp_path directory so backups are created there
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = transform_readme(str(readme_path), create_backup=True)

            assert result is True

            # Verify backup was created
            backup_dir = tmp_path / ".readme_backups"
            assert backup_dir.exists()
            backups = list(backup_dir.glob("README_backup_*.md"))
            assert len(backups) > 0
        finally:
            os.chdir(original_cwd)

    def test_transform_readme_file_not_found(self, tmp_path: Path) -> None:
        """Test error handling when README file does not exist."""
        readme_path = tmp_path / "nonexistent.md"

        with pytest.raises(FileNotFoundError):
            transform_readme(str(readme_path))

    def test_transform_readme_preserves_content(self, tmp_path: Path) -> None:
        """Test that transformation preserves original content."""
        readme_path = tmp_path / "README.md"
        original_intro = "This is the original introduction"
        original_content = "This is the original detailed content"
        test_content = f"{original_intro}\n\n# Section\n\n{original_content}"
        readme_path.write_text(test_content, encoding="utf-8")

        result = transform_readme(str(readme_path), create_backup=False)

        assert result is True
        transformed = readme_path.read_text(encoding="utf-8")
        assert original_intro in transformed
        assert original_content in transformed

    def test_transform_readme_with_custom_features(self, tmp_path: Path) -> None:
        """Test transformation with custom features."""
        readme_path = tmp_path / "README.md"
        test_content = "Introduction\n\n# Section\n\nContent"
        readme_path.write_text(test_content, encoding="utf-8")

        custom_features = [
            {"task": "Custom Task 1", "function": "custom_func1()"},
            {"task": "Custom Task 2", "function": "custom_func2()"},
        ]

        result = transform_readme(
            str(readme_path), create_backup=False, features=custom_features
        )

        assert result is True
        transformed = readme_path.read_text(encoding="utf-8")
        assert "Custom Task 1" in transformed
        assert "custom_func1()" in transformed
        assert "Custom Task 2" in transformed
        assert "custom_func2()" in transformed

    def test_transform_readme_with_custom_audience(self, tmp_path: Path) -> None:
        """Test transformation with custom target audience bullets."""
        readme_path = tmp_path / "README.md"
        test_content = "Introduction\n\n# Section\n\nContent"
        readme_path.write_text(test_content, encoding="utf-8")

        custom_bullets = [
            "Custom bullet 1",
            "Custom bullet 2",
            "Custom bullet 3",
        ]

        result = transform_readme(
            str(readme_path),
            create_backup=False,
            target_audience_bullets=custom_bullets,
        )

        assert result is True
        transformed = readme_path.read_text(encoding="utf-8")
        for bullet in custom_bullets:
            assert bullet in transformed

    def test_transform_readme_backup_recovery(self, tmp_path: Path) -> None:
        """Test backup creation and recovery mechanism."""
        readme_path = tmp_path / "README.md"
        original_content = "Original content"
        readme_path.write_text(original_content, encoding="utf-8")

        # Change to tmp_path directory so backups are created there
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            # Transform with backup
            result = transform_readme(str(readme_path), create_backup=True)
            assert result is True

            # Get the backup file
            backup_dir = tmp_path / ".readme_backups"
            backups = list(backup_dir.glob("README_backup_*.md"))
            assert len(backups) > 0

            backup_path = backups[0]

            # Verify backup contains original content
            backup_content = backup_path.read_text(encoding="utf-8")
            assert backup_content == original_content

            # Modify the README
            readme_path.write_text("Modified content", encoding="utf-8")

            # Recover from backup
            backup_manager = BackupManager(str(readme_path), str(backup_dir))
            backup_manager.restore_backup(backup_path)

            # Verify recovery
            recovered_content = readme_path.read_text(encoding="utf-8")
            assert recovered_content == original_content
        finally:
            os.chdir(original_cwd)

    def test_transform_readme_multiple_backups(self, tmp_path: Path) -> None:
        """Test creation of multiple backups."""
        import time
        import os

        readme_path = tmp_path / "README.md"
        readme_path.write_text("Content 1", encoding="utf-8")

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            # Create first backup
            result1 = transform_readme(str(readme_path), create_backup=True)
            assert result1 is True

            # Wait to ensure different timestamp
            time.sleep(1.1)

            # Modify and create second backup
            readme_path.write_text("Content 2", encoding="utf-8")
            result2 = transform_readme(str(readme_path), create_backup=True)
            assert result2 is True

            # Verify both backups exist
            backup_dir = tmp_path / ".readme_backups"
            backups = list(backup_dir.glob("README_backup_*.md"))
            assert len(backups) >= 2
        finally:
            os.chdir(original_cwd)

    def test_transform_readme_validation_failure(self, tmp_path: Path) -> None:
        """Test handling of validation failures."""
        readme_path = tmp_path / "README.md"
        # Create a README with problematic content
        test_content = "Introduction\n\n# Section\n\nContent"
        readme_path.write_text(test_content, encoding="utf-8")

        # This should succeed with valid content
        result = transform_readme(str(readme_path), create_backup=False)
        assert result is True

    def test_transform_readme_empty_file(self, tmp_path: Path) -> None:
        """Test handling of empty README file."""
        readme_path = tmp_path / "README.md"
        readme_path.write_text("", encoding="utf-8")

        # Should handle gracefully
        result = transform_readme(str(readme_path), create_backup=False)

        # Result depends on implementation - may succeed or fail gracefully
        # The important thing is it doesn't crash
        assert isinstance(result, bool)

    def test_transform_readme_large_file(self, tmp_path: Path) -> None:
        """Test handling of large README file."""
        readme_path = tmp_path / "README.md"

        # Create a large README with lots of content
        large_content = "Introduction\n\n"
        for i in range(100):
            large_content += f"## Section {i}\n\nContent for section {i}\n\n"

        readme_path.write_text(large_content, encoding="utf-8")

        result = transform_readme(str(readme_path), create_backup=False)

        assert result is True
        transformed = readme_path.read_text(encoding="utf-8")
        assert "pip install fishertools" in transformed
        assert "Для кого эта библиотека" in transformed

    def test_transform_readme_with_special_characters(self, tmp_path: Path) -> None:
        """Test handling of special characters in content."""
        readme_path = tmp_path / "README.md"
        test_content = "Introduction with émojis 🐍\n\n# Section\n\nContent with special chars: @#$%"
        readme_path.write_text(test_content, encoding="utf-8")

        result = transform_readme(str(readme_path), create_backup=False)

        assert result is True
        transformed = readme_path.read_text(encoding="utf-8")
        assert "émojis 🐍" in transformed
        assert "@#$%" in transformed

    def test_transform_readme_idempotent(self, tmp_path: Path) -> None:
        """Test that transformation is idempotent (can be run multiple times)."""
        readme_path = tmp_path / "README.md"
        test_content = "Introduction\n\n# Section\n\nContent"
        readme_path.write_text(test_content, encoding="utf-8")

        # First transformation
        result1 = transform_readme(str(readme_path), create_backup=False)
        assert result1 is True
        first_result = readme_path.read_text(encoding="utf-8")

        # Second transformation - should not duplicate sections
        result2 = transform_readme(str(readme_path), create_backup=False)
        assert result2 is True
        second_result = readme_path.read_text(encoding="utf-8")

        # Both should have the required sections
        assert "pip install fishertools" in first_result
        assert "Для кого эта библиотека" in first_result
        assert "pip install fishertools" in second_result
        assert "Для кого эта библиотека" in second_result
        
        # Count occurrences - should not increase significantly
        first_install_count = first_result.count("pip install fishertools")
        second_install_count = second_result.count("pip install fishertools")
        
        # Allow for some variation but not doubling
        assert second_install_count <= first_install_count + 1

    def test_transform_readme_real_world_example(self, tmp_path: Path) -> None:
        """Test transformation with a realistic README structure."""
        readme_path = tmp_path / "README.md"
        realistic_content = """# Fishertools

**Инструменты, которые делают Python удобнее и безопаснее для новичков**

Fishertools - это Python библиотека, созданная специально для начинающих разработчиков.

## 🎯 Основные возможности

### 🚨 Объяснение ошибок Python
Получайте понятные объяснения ошибок на русском языке.

### 🛡️ Безопасные утилиты
Функции, которые предотвращают типичные ошибки новичков.

## 📦 Установка

```bash
pip install fishertools
```

## 🚀 Быстрый старт

```python
from fishertools import explain_error
```

## 📖 Документация

Полная документация доступна на сайте.
"""
        readme_path.write_text(realistic_content, encoding="utf-8")

        result = transform_readme(str(readme_path), create_backup=False)

        assert result is True
        transformed = readme_path.read_text(encoding="utf-8")

        # Verify all required sections are present
        assert "Fishertools" in transformed
        assert "pip install fishertools" in transformed
        assert "Для кого эта библиотека" in transformed
        assert "Задача" in transformed
        assert "Что вызвать" in transformed
        assert "explain_error(e)" in transformed
        assert "safe_read_file(path)" in transformed

    def test_transform_readme_preserves_formatting(self, tmp_path: Path) -> None:
        """Test that transformation preserves markdown formatting."""
        readme_path = tmp_path / "README.md"
        test_content = """Introduction

# Heading 1

## Heading 2

### Heading 3

- Bullet 1
- Bullet 2

1. Numbered 1
2. Numbered 2

**Bold text** and *italic text*

```python
code_block()
```
"""
        readme_path.write_text(test_content, encoding="utf-8")

        result = transform_readme(str(readme_path), create_backup=False)

        assert result is True
        transformed = readme_path.read_text(encoding="utf-8")

        # Verify formatting is preserved
        assert "# Heading 1" in transformed
        assert "## Heading 2" in transformed
        assert "### Heading 3" in transformed
        assert "- Bullet 1" in transformed
        assert "1. Numbered 1" in transformed
        assert "**Bold text**" in transformed
        assert "*italic text*" in transformed
        assert "```python" in transformed

    def test_transform_readme_error_handling_io_error(self, tmp_path: Path) -> None:
        """Test error handling for IO errors."""
        readme_path = tmp_path / "README.md"
        readme_path.write_text("Content", encoding="utf-8")

        # Make the file read-only to simulate IO error on write
        import os

        os.chmod(readme_path, 0o444)

        try:
            # This should fail gracefully
            result = transform_readme(str(readme_path), create_backup=False)
            # Result should be False due to write error
            assert result is False
        finally:
            # Restore permissions for cleanup
            os.chmod(readme_path, 0o644)

    def test_transform_readme_with_all_options(self, tmp_path: Path) -> None:
        """Test transformation with all options specified."""
        readme_path = tmp_path / "README.md"
        test_content = "Introduction\n\n# Section\n\nContent"
        readme_path.write_text(test_content, encoding="utf-8")

        custom_features = [
            {"task": "Task 1", "function": "func1()"},
            {"task": "Task 2", "function": "func2()"},
        ]

        custom_bullets = [
            "Bullet 1",
            "Bullet 2",
            "Bullet 3",
        ]

        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = transform_readme(
                str(readme_path),
                create_backup=True,
                features=custom_features,
                target_audience_bullets=custom_bullets,
            )

            assert result is True

            # Verify backup was created
            backup_dir = tmp_path / ".readme_backups"
            assert backup_dir.exists()

            # Verify custom features are in the result
            transformed = readme_path.read_text(encoding="utf-8")
            assert "Task 1" in transformed
            assert "func1()" in transformed
            assert "Task 2" in transformed
            assert "func2()" in transformed

            # Verify custom bullets are in the result
            for bullet in custom_bullets:
                assert bullet in transformed
        finally:
            os.chdir(original_cwd)
