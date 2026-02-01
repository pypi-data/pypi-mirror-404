"""Integration tests for Phase 1 modules (v0.5.0)."""

import pytest
from fishertools.visualization import visualize
from fishertools.validation import validate_types, validate_structure, ValidationError
from fishertools.debug import debug_step_by_step


class TestPhase1Integration:
    """Integration tests for all Phase 1 modules."""

    def test_visualization_with_validation(self):
        """Test visualization with validated data."""

        @validate_types
        def create_data(items: list) -> dict:
            return {"items": items, "count": len(items)}

        data = create_data([1, 2, 3, 4, 5])
        result = visualize(data, title="Validated Data")

        assert "Validated Data" in result
        assert "items" in result
        assert "count" in result

    def test_validation_with_debug(self, capsys):
        """Test validation with debug decorator."""

        @validate_types
        @debug_step_by_step
        def process_numbers(numbers: list) -> int:
            total = sum(numbers)
            return total

        result = process_numbers([1, 2, 3, 4, 5])
        captured = capsys.readouterr()

        assert result == 15
        assert "Debugging" in captured.out
        assert "numbers" in captured.out

    def test_all_three_modules(self, capsys):
        """Test all three modules working together."""

        @validate_types
        @debug_step_by_step
        def analyze_data(data: dict) -> dict:
            # Validate structure
            schema = {"name": str, "values": list}
            validate_structure(data, schema)

            # Visualize input
            visualize(data, title="Input Data")

            # Process
            result = {
                "name": data["name"],
                "count": len(data["values"]),
                "sum": sum(data["values"]),
            }

            # Visualize output
            visualize(result, title="Output Data")

            return result

        input_data = {"name": "Test", "values": [1, 2, 3, 4, 5]}
        result = analyze_data(input_data)

        assert result["name"] == "Test"
        assert result["count"] == 5
        assert result["sum"] == 15

    def test_validation_error_with_visualization(self):
        """Test validation error doesn't break visualization."""

        @validate_types
        def create_user(name: str, age: int) -> dict:
            return {"name": name, "age": age}

        # Valid call
        user = create_user("Alice", 25)
        result = visualize(user)
        assert "Alice" in result
        assert "25" in result

        # Invalid call
        with pytest.raises(ValidationError):
            create_user("Bob", "thirty")

    def test_complex_nested_validation_and_visualization(self):
        """Test complex nested structures with validation and visualization."""

        @validate_types
        def create_organization(name: str, departments: list) -> dict:
            return {"name": name, "departments": departments}

        org = create_organization(
            "TechCorp",
            [
                {"name": "Engineering", "size": 50},
                {"name": "Sales", "size": 30},
                {"name": "HR", "size": 10},
            ],
        )

        result = visualize(org, title="Organization Structure")

        assert "Organization Structure" in result
        assert "TechCorp" in result
        assert "Engineering" in result

    def test_debug_with_validation_error(self, capsys):
        """Test debug decorator with validation error."""

        @validate_types
        @debug_step_by_step
        def divide(a: int, b: int) -> float:
            result = a / b
            return result

        # Valid call
        result = divide(10, 2)
        assert abs(result - 5.0) < 1e-9

        # Invalid call
        with pytest.raises(ValidationError):
            divide(10, "two")

    def test_visualization_of_validated_structure(self):
        """Test visualizing a validated data structure."""

        schema = {"id": int, "name": str, "active": bool}

        @validate_types
        def create_record(id: int, name: str, active: bool) -> dict:
            record = {"id": id, "name": name, "active": active}
            validate_structure(record, schema)
            return record

        record = create_record(1, "Alice", True)
        result = visualize(record, title="Record")

        assert "Record" in result
        assert "Alice" in result
        assert "True" in result

    def test_multiple_validations_with_visualization(self):
        """Test multiple validation checks with visualization."""

        @validate_types
        def process_batch(items: list) -> dict:
            # Validate each item
            for item in items:
                validate_structure(item, {"id": int, "value": float})

            # Visualize
            result = {"count": len(items), "items": items}
            visualize(result, title="Batch")

            return result

        items = [
            {"id": 1, "value": 10.5},
            {"id": 2, "value": 20.3},
            {"id": 3, "value": 15.7},
        ]

        result = process_batch(items)
        assert result["count"] == 3

    def test_error_handling_across_modules(self):
        """Test error handling across all modules."""

        @validate_types
        def safe_process(data: dict) -> dict:
            try:
                validate_structure(data, {"name": str, "age": int})
                visualize(data)
                return {"status": "success", "data": data}
            except ValidationError as e:
                return {"status": "error", "message": str(e)}

        # Valid data
        result = safe_process({"name": "Alice", "age": 25})
        assert result["status"] == "success"

        # Invalid data
        result = safe_process({"name": "Bob", "age": "thirty"})
        assert result["status"] == "error"
        assert "age" in result["message"]
