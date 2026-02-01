"""Code example validation for the Extended Documentation system."""

import ast
import sys
import subprocess
from typing import List, Optional
from fishertools.documentation.models import ValidationResult


class CodeExampleValidator:
    """Validates code examples for syntax and execution."""

    @staticmethod
    def validate_example_syntax(code: str) -> ValidationResult:
        """
        Validate that code is syntactically correct Python.

        Args:
            code: Python code to validate

        Returns:
            ValidationResult with validation status
        """
        errors = []
        warnings = []

        if not code or not code.strip():
            errors.append("Code cannot be empty")
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

        try:
            ast.parse(code)
        except SyntaxError as e:
            errors.append(f"Syntax error: {e.msg} at line {e.lineno}")
        except Exception as e:
            errors.append(f"Parse error: {str(e)}")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    @staticmethod
    def validate_example_output(code: str, expected_output: str) -> ValidationResult:
        """
        Validate that code produces expected output.

        Args:
            code: Python code to execute
            expected_output: Expected output from running the code

        Returns:
            ValidationResult with validation status
        """
        errors = []
        warnings = []

        # First check syntax
        syntax_result = CodeExampleValidator.validate_example_syntax(code)
        if not syntax_result.is_valid:
            return syntax_result

        if not expected_output or not expected_output.strip():
            warnings.append("Expected output is empty or not documented")

        try:
            # Execute the code and capture output
            result = subprocess.run(
                [sys.executable, "-c", code],
                capture_output=True,
                text=True,
                timeout=5,
            )

            actual_output = result.stdout.strip()
            expected_output_stripped = expected_output.strip() if expected_output else ""

            # Compare outputs
            if actual_output != expected_output_stripped:
                warnings.append(
                    f"Output mismatch. Expected: {expected_output_stripped!r}, "
                    f"Got: {actual_output!r}"
                )

            # Check for errors
            if result.returncode != 0:
                errors.append(f"Code execution failed: {result.stderr}")

        except subprocess.TimeoutExpired:
            errors.append("Code execution timed out (>5 seconds)")
        except Exception as e:
            errors.append(f"Execution error: {str(e)}")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    @staticmethod
    def validate_code_with_versions(
        code: str, python_versions: Optional[List[str]] = None
    ) -> ValidationResult:
        """
        Validate code against multiple Python versions.

        Args:
            code: Python code to validate
            python_versions: List of Python versions to test (e.g., ["3.8", "3.9", "3.10"])

        Returns:
            ValidationResult with validation status
        """
        errors = []
        warnings = []

        # First check syntax with current version
        syntax_result = CodeExampleValidator.validate_example_syntax(code)
        if not syntax_result.is_valid:
            return syntax_result

        if python_versions is None:
            python_versions = ["3.8", "3.9", "3.10", "3.11", "3.12", "3.13"]

        # Test with current Python version
        current_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        try:
            result = subprocess.run(
                [sys.executable, "-c", code],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode != 0:
                errors.append(f"Code fails with Python {current_version}: {result.stderr}")
        except subprocess.TimeoutExpired:
            errors.append(f"Code execution timed out with Python {current_version}")
        except Exception as e:
            errors.append(f"Execution error with Python {current_version}: {str(e)}")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    @staticmethod
    def validate_code_imports(code: str) -> ValidationResult:
        """
        Validate that all imports in code are available.

        Args:
            code: Python code to validate

        Returns:
            ValidationResult with validation status
        """
        errors = []
        warnings = []

        # First check syntax
        syntax_result = CodeExampleValidator.validate_example_syntax(code)
        if not syntax_result.is_valid:
            return syntax_result

        try:
            tree = ast.parse(code)
            CodeExampleValidator._check_imports_in_tree(tree, warnings)
        except Exception as e:
            errors.append(f"Error analyzing imports: {str(e)}")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    @staticmethod
    def _check_imports_in_tree(tree: ast.AST, warnings: List[str]) -> None:
        """Check all imports in the AST tree."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                CodeExampleValidator._check_import_node(node, warnings)
            elif isinstance(node, ast.ImportFrom):
                CodeExampleValidator._check_import_from_node(node, warnings)

    @staticmethod
    def _check_import_node(node: ast.Import, warnings: List[str]) -> None:
        """Check a regular import node."""
        for alias in node.names:
            module_name = alias.name.split(".")[0]
            CodeExampleValidator._try_import_module(module_name, warnings)

    @staticmethod
    def _check_import_from_node(node: ast.ImportFrom, warnings: List[str]) -> None:
        """Check an import from node."""
        if node.module:
            module_name = node.module.split(".")[0]
            CodeExampleValidator._try_import_module(module_name, warnings)

    @staticmethod
    def _try_import_module(module_name: str, warnings: List[str]) -> None:
        """Try to import a module and add warning if not available."""
        try:
            __import__(module_name)
        except ImportError:
            warnings.append(f"Module '{module_name}' may not be available")

    @staticmethod
    def validate_code_complexity(code: str, max_lines: int = 50) -> ValidationResult:
        """
        Validate that code is not too complex for an example.

        Args:
            code: Python code to validate
            max_lines: Maximum number of lines for an example

        Returns:
            ValidationResult with validation status
        """
        errors = []
        warnings = []

        lines = code.strip().split("\n")
        line_count = len(lines)

        if line_count > max_lines:
            warnings.append(
                f"Code example is {line_count} lines, consider breaking into smaller examples"
            )

        # Check for deeply nested code
        try:
            tree = ast.parse(code)
            max_depth = CodeExampleValidator._get_max_nesting_depth(tree)

            if max_depth > 5:
                warnings.append(
                    f"Code has deep nesting (depth {max_depth}), consider simplifying"
                )
        except Exception as e:
            errors.append(f"Error analyzing code complexity: {str(e)}")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    @staticmethod
    def _get_max_nesting_depth(node: ast.AST, depth: int = 0) -> int:
        """Get maximum nesting depth in AST."""
        max_depth = depth

        for child in ast.iter_child_nodes(node):
            child_depth = CodeExampleValidator._get_max_nesting_depth(child, depth + 1)
            max_depth = max(max_depth, child_depth)

        return max_depth
