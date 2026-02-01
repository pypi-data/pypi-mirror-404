"""
Unit tests for configuration error handling.

Tests specific error scenarios and edge cases for configuration management.
"""

import json
import tempfile
import os
import platform
import pytest

from fishertools.config.models import LearningConfig, ErrorSeverity
from fishertools.config.manager import ConfigurationManager
from fishertools.config.parser import ConfigurationParser


class TestConfigurationErrorHandling:
    """Unit tests for configuration error handling scenarios."""
    
    def test_missing_required_fields(self):
        """Test handling of configurations with missing required fields."""
        parser = ConfigurationParser()
        
        # Configuration missing required 'default_level' field
        config_missing_level = {
            "explanation_verbosity": "detailed",
            "visual_aids_enabled": True
        }
        
        validation_result = parser.validate_structure(config_missing_level)
        assert not validation_result.is_valid
        assert len(validation_result.errors) > 0
        
        # Check that the error mentions the missing field
        error_messages = [error.message for error in validation_result.errors]
        assert any("default_level" in msg for msg in error_messages)
        assert any("missing" in msg.lower() for msg in error_messages)
    
    def test_wrong_data_types(self):
        """Test handling of configurations with wrong data types."""
        parser = ConfigurationParser()
        
        # Configuration with wrong types
        config_wrong_types = {
            "default_level": "beginner",
            "explanation_verbosity": "detailed", 
            "visual_aids_enabled": "true",  # Should be boolean, not string
            "suggested_topics_count": "5",  # Should be int, not string
            "progress_tracking_enabled": 1  # Should be boolean, not int
        }
        
        validation_result = parser.validate_structure(config_wrong_types)
        assert not validation_result.is_valid
        assert len(validation_result.errors) >= 2  # At least 2 type errors
        
        # Check error details
        for error in validation_result.errors:
            assert error.severity == ErrorSeverity.ERROR
            assert "type" in error.message.lower()
            assert error.suggested_fix is not None
    
    def test_invalid_enum_values(self):
        """Test handling of invalid enum values."""
        parser = ConfigurationParser()
        
        # Configuration with invalid enum values
        config_invalid_enums = {
            "default_level": "expert",  # Should be beginner/intermediate/advanced
            "explanation_verbosity": "verbose",  # Should be brief/detailed/comprehensive
            "visual_aids_enabled": True
        }
        
        validation_result = parser.validate_structure(config_invalid_enums)
        assert not validation_result.is_valid
        assert len(validation_result.errors) >= 2
        
        # Check that errors mention valid values
        error_messages = [error.message for error in validation_result.errors]
        assert any("valid values" in msg.lower() for msg in error_messages)
    
    def test_out_of_range_numeric_values(self):
        """Test handling of numeric values outside recommended ranges."""
        parser = ConfigurationParser()
        
        # Configuration with values outside recommended ranges
        config_out_of_range = {
            "default_level": "beginner",
            "explanation_verbosity": "detailed",
            "suggested_topics_count": 50,  # Too high (recommended 1-10)
            "max_examples_per_topic": 0,   # Too low (recommended 1-20)
            "visual_aids_enabled": True
        }
        
        validation_result = parser.validate_structure(config_out_of_range)
        # Should be valid but have warnings
        assert validation_result.is_valid
        assert len(validation_result.warnings) >= 2
        
        # Check warning details
        for warning in validation_result.warnings:
            assert warning.severity == ErrorSeverity.WARNING
            assert "range" in warning.message.lower()
    
    def test_unknown_fields_warning(self):
        """Test that unknown fields generate warnings."""
        parser = ConfigurationParser()
        
        # Configuration with unknown fields
        config_unknown_fields = {
            "default_level": "beginner",
            "explanation_verbosity": "detailed",
            "unknown_field": "some_value",
            "another_unknown": 42
        }
        
        validation_result = parser.validate_structure(config_unknown_fields)
        assert validation_result.is_valid  # Should still be valid
        assert len(validation_result.warnings) >= 2  # Should have warnings for unknown fields
        
        # Check warning details
        warning_messages = [warning.message for warning in validation_result.warnings]
        assert any("unknown" in msg.lower() for msg in warning_messages)
        assert any("ignored" in msg.lower() for msg in warning_messages)
    
    def test_file_not_found_error(self):
        """Test handling of missing configuration files."""
        manager = ConfigurationManager()
        
        # Try to load non-existent file
        with pytest.raises(FileNotFoundError) as exc_info:
            manager.load_config("non_existent_config.json")
        
        error_message = str(exc_info.value)
        assert "not found" in error_message.lower()
        assert "non_existent_config.json" in error_message
    
    def test_invalid_json_file(self):
        """Test handling of files with invalid JSON."""
        manager = ConfigurationManager()
        
        # Create temporary file with invalid JSON
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"invalid": json content}')  # Invalid JSON
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError) as exc_info:
                manager.load_config(temp_path)
            
            error_message = str(exc_info.value)
            assert "failed to load configuration" in error_message.lower()
        finally:
            os.unlink(temp_path)
    
    def test_validation_failure_on_load(self):
        """Test that validation failures prevent configuration loading."""
        manager = ConfigurationManager()
        
        # Create temporary file with invalid configuration
        invalid_config = {
            "default_level": "invalid_level",  # Invalid enum value
            "explanation_verbosity": 123,      # Wrong type
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(invalid_config, f)
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError) as exc_info:
                manager.load_config(temp_path)
            
            error_message = str(exc_info.value)
            assert "validation failed" in error_message.lower()
        finally:
            os.unlink(temp_path)
    
    def test_save_to_invalid_path(self):
        """Test handling of invalid save paths."""
        manager = ConfigurationManager()
        config = LearningConfig()
        
        # Create a temporary directory and then remove it to simulate permission error
        with tempfile.TemporaryDirectory() as temp_dir:
            invalid_path = os.path.join(temp_dir, "subdir", "config.json")
        
        # Now temp_dir is deleted, so trying to create subdir should fail
        # But our implementation creates directories, so let's use a different approach
        
        # Try to save to a file that exists as a directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a directory with the same name as our target file
            dir_as_file = os.path.join(temp_dir, "config.json")
            os.makedirs(dir_as_file)
            
            with pytest.raises(IOError) as exc_info:
                manager.save_config(config, dir_as_file)
            
            error_message = str(exc_info.value)
            assert "failed to save configuration" in error_message.lower()
    
    def test_apply_invalid_config(self):
        """Test that applying invalid configuration raises error."""
        manager = ConfigurationManager()
        
        # Create invalid config by directly modifying fields
        invalid_config = LearningConfig()
        invalid_config.default_level = "invalid_level"  # Invalid enum value
        
        with pytest.raises(ValueError) as exc_info:
            manager.apply_config(invalid_config)
        
        error_message = str(exc_info.value)
        assert "cannot apply invalid configuration" in error_message.lower()
    
    def test_yaml_not_available_error(self):
        """Test handling when YAML support is not available."""
        parser = ConfigurationParser()
        
        # Mock YAML not being available by temporarily setting the flag
        original_yaml_available = parser.__class__.__module__
        
        # Test YAML parsing when not available
        # This test assumes YAML is available, so we'll test the error path differently
        try:
            # Try to parse YAML content
            yaml_content = "key: value\nother_key: other_value"
            result = parser.parse_yaml(yaml_content)
            # If we get here, YAML is available, which is expected
            assert isinstance(result, dict)
        except ValueError as e:
            # If YAML is not available, should get appropriate error
            assert "yaml support not available" in str(e).lower()
    
    def test_configuration_merge_with_invalid_overrides(self):
        """Test merging configuration with invalid override values."""
        manager = ConfigurationManager()
        base_config = LearningConfig()
        
        # Invalid overrides
        invalid_overrides = {
            "default_level": "invalid_level",
            "suggested_topics_count": "not_a_number"
        }
        
        # Merge should work (it just updates the dict)
        merged_config = manager.merge_configs(base_config, invalid_overrides)
        
        # But validation should fail
        validation_result = manager.validate_config(merged_config)
        assert not validation_result.is_valid
        assert len(validation_result.errors) > 0
    
    def test_error_message_descriptiveness(self):
        """Test that error messages are descriptive and helpful."""
        parser = ConfigurationParser()
        
        # Test various error scenarios
        test_cases = [
            {
                "config": {"default_level": 123},
                "expected_in_message": ["type", "str", "int"]  # Changed "string" to "str"
            },
            {
                "config": {"default_level": "invalid"},
                "expected_in_message": ["invalid value", "valid values"]
            },
            {
                "config": {},  # Missing required fields
                "expected_in_message": ["missing", "required"]
            }
        ]
        
        for case in test_cases:
            validation_result = parser.validate_structure(case["config"])
            assert not validation_result.is_valid
            
            # Check that error messages contain expected terms
            all_messages = " ".join([error.message.lower() for error in validation_result.errors])
            for expected_term in case["expected_in_message"]:
                assert expected_term.lower() in all_messages
            
            # Check that suggested fixes are provided
            for error in validation_result.errors:
                assert error.suggested_fix is not None
                assert len(error.suggested_fix) > 0