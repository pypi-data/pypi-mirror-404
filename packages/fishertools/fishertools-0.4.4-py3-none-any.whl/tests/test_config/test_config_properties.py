"""
Property-based tests for configuration management.

Feature: fishertools-enhancements
"""

import json
import tempfile
import os
from hypothesis import given, strategies as st, assume
import pytest

from fishertools.config.models import LearningConfig
from fishertools.config.manager import ConfigurationManager
from fishertools.config.parser import ConfigurationParser


def _is_valid_json(text: str) -> bool:
    """Helper function to check if text is valid JSON."""
    try:
        json.loads(text)
        return True
    except (json.JSONDecodeError, ValueError):
        return False


# Strategy for generating valid LearningConfig objects
@st.composite
def learning_config_strategy(draw):
    """Generate valid LearningConfig objects for property testing."""
    return LearningConfig(
        default_level=draw(st.sampled_from(["beginner", "intermediate", "advanced"])),
        explanation_verbosity=draw(st.sampled_from(["brief", "detailed", "comprehensive"])),
        visual_aids_enabled=draw(st.booleans()),
        diagram_style=draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        color_scheme=draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        progress_tracking_enabled=draw(st.booleans()),
        save_progress_locally=draw(st.booleans()),
        suggested_topics_count=draw(st.integers(min_value=1, max_value=10)),
        max_examples_per_topic=draw(st.integers(min_value=1, max_value=20)),
        exercise_difficulty_progression=draw(st.lists(
            st.sampled_from(["beginner", "intermediate", "advanced"]),
            min_size=1, max_size=5
        )),
        readthedocs_project=draw(st.one_of(
            st.none(),
            st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc')))
        )),
        sphinx_theme=draw(st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc')))),
        enable_interactive_sessions=draw(st.booleans()),
        session_timeout_minutes=draw(st.integers(min_value=1, max_value=180)),
        max_hint_count=draw(st.integers(min_value=0, max_value=10))
    )


# Strategy for generating valid configuration dictionaries
@st.composite
def valid_config_dict_strategy(draw):
    """Generate valid configuration dictionaries for property testing."""
    return {
        "default_level": draw(st.sampled_from(["beginner", "intermediate", "advanced"])),
        "explanation_verbosity": draw(st.sampled_from(["brief", "detailed", "comprehensive"])),
        "visual_aids_enabled": draw(st.booleans()),
        "diagram_style": draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        "color_scheme": draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        "progress_tracking_enabled": draw(st.booleans()),
        "save_progress_locally": draw(st.booleans()),
        "suggested_topics_count": draw(st.integers(min_value=1, max_value=10)),
        "max_examples_per_topic": draw(st.integers(min_value=1, max_value=20)),
        "exercise_difficulty_progression": draw(st.lists(
            st.sampled_from(["beginner", "intermediate", "advanced"]),
            min_size=1, max_size=5
        )),
        "readthedocs_project": draw(st.one_of(
            st.none(),
            st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc')))
        )),
        "sphinx_theme": draw(st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc')))),
        "enable_interactive_sessions": draw(st.booleans()),
        "session_timeout_minutes": draw(st.integers(min_value=1, max_value=180)),
        "max_hint_count": draw(st.integers(min_value=0, max_value=10))
    }


# Strategy for generating invalid configuration dictionaries
@st.composite
def invalid_config_dict_strategy(draw):
    """Generate invalid configuration dictionaries for property testing."""
    config = {}
    
    # Add some valid fields
    if draw(st.booleans()):
        config["default_level"] = draw(st.sampled_from(["beginner", "intermediate", "advanced"]))
    
    # Add invalid fields with wrong types or values
    invalid_choices = draw(st.sampled_from([
        "wrong_type_level",
        "wrong_type_verbosity", 
        "wrong_type_bool",
        "wrong_type_int",
        "invalid_enum_value",
        "missing_required"
    ]))
    
    if invalid_choices == "wrong_type_level":
        config["default_level"] = draw(st.integers())  # Should be string
    elif invalid_choices == "wrong_type_verbosity":
        config["explanation_verbosity"] = draw(st.integers())  # Should be string
    elif invalid_choices == "wrong_type_bool":
        config["visual_aids_enabled"] = draw(st.text())  # Should be bool
    elif invalid_choices == "wrong_type_int":
        config["suggested_topics_count"] = draw(st.text())  # Should be int
    elif invalid_choices == "invalid_enum_value":
        config["default_level"] = draw(st.text().filter(lambda x: x not in ["beginner", "intermediate", "advanced"]))
        config["explanation_verbosity"] = "detailed"  # Add required field
    elif invalid_choices == "missing_required":
        # Don't add required fields
        config["visual_aids_enabled"] = True
    
    return config


class TestConfigurationRoundTrip:
    """Property tests for configuration round-trip serialization."""
    
    @given(config=learning_config_strategy())
    def test_json_round_trip_property(self, config):
        """
        Property 8: Configuration Serialization Round-trip (JSON)
        
        For any valid configuration object, parsing then formatting then parsing 
        should produce an equivalent configuration object.
        
        Validates: Requirements 7.4
        """
        # Feature: fishertools-enhancements, Property 8: Configuration Serialization Round-trip
        
        parser = ConfigurationParser()
        manager = ConfigurationManager()
        
        # Format config to JSON
        json_content = parser.format_to_json(config)
        
        # Parse JSON back to dict
        parsed_dict = parser.parse_json(json_content)
        
        # Convert back to LearningConfig
        reconstructed_config = manager._dict_to_config(parsed_dict)
        
        # Verify equivalence
        assert reconstructed_config.default_level == config.default_level
        assert reconstructed_config.explanation_verbosity == config.explanation_verbosity
        assert reconstructed_config.visual_aids_enabled == config.visual_aids_enabled
        assert reconstructed_config.diagram_style == config.diagram_style
        assert reconstructed_config.color_scheme == config.color_scheme
        assert reconstructed_config.progress_tracking_enabled == config.progress_tracking_enabled
        assert reconstructed_config.save_progress_locally == config.save_progress_locally
        assert reconstructed_config.suggested_topics_count == config.suggested_topics_count
        assert reconstructed_config.max_examples_per_topic == config.max_examples_per_topic
        assert reconstructed_config.exercise_difficulty_progression == config.exercise_difficulty_progression
        assert reconstructed_config.readthedocs_project == config.readthedocs_project
        assert reconstructed_config.sphinx_theme == config.sphinx_theme
        assert reconstructed_config.enable_interactive_sessions == config.enable_interactive_sessions
        assert reconstructed_config.session_timeout_minutes == config.session_timeout_minutes
        assert reconstructed_config.max_hint_count == config.max_hint_count
    
    @given(config=learning_config_strategy())
    def test_yaml_round_trip_property(self, config):
        """
        Property 8: Configuration Serialization Round-trip (YAML)
        
        For any valid configuration object, parsing then formatting then parsing 
        should produce an equivalent configuration object.
        
        Validates: Requirements 7.4
        """
        # Feature: fishertools-enhancements, Property 8: Configuration Serialization Round-trip
        
        parser = ConfigurationParser()
        manager = ConfigurationManager()
        
        try:
            # Format config to YAML
            yaml_content = parser.format_to_yaml(config)
            
            # Parse YAML back to dict
            parsed_dict = parser.parse_yaml(yaml_content)
            
            # Convert back to LearningConfig
            reconstructed_config = manager._dict_to_config(parsed_dict)
            
            # Verify equivalence
            assert reconstructed_config.default_level == config.default_level
            assert reconstructed_config.explanation_verbosity == config.explanation_verbosity
            assert reconstructed_config.visual_aids_enabled == config.visual_aids_enabled
            assert reconstructed_config.diagram_style == config.diagram_style
            assert reconstructed_config.color_scheme == config.color_scheme
            assert reconstructed_config.progress_tracking_enabled == config.progress_tracking_enabled
            assert reconstructed_config.save_progress_locally == config.save_progress_locally
            assert reconstructed_config.suggested_topics_count == config.suggested_topics_count
            assert reconstructed_config.max_examples_per_topic == config.max_examples_per_topic
            assert reconstructed_config.exercise_difficulty_progression == config.exercise_difficulty_progression
            assert reconstructed_config.readthedocs_project == config.readthedocs_project
            assert reconstructed_config.sphinx_theme == config.sphinx_theme
            assert reconstructed_config.enable_interactive_sessions == config.enable_interactive_sessions
            assert reconstructed_config.session_timeout_minutes == config.session_timeout_minutes
            assert reconstructed_config.max_hint_count == config.max_hint_count
            
        except ValueError as e:
            if "YAML support not available" in str(e):
                pytest.skip("YAML support not available")
            else:
                raise
    
    @given(config=learning_config_strategy())
    def test_file_round_trip_property_json(self, config):
        """
        Property 8: Configuration Serialization Round-trip (File I/O JSON)
        
        For any valid configuration object, saving to file then loading 
        should produce an equivalent configuration object.
        
        Validates: Requirements 7.4
        """
        # Feature: fishertools-enhancements, Property 8: Configuration Serialization Round-trip
        
        manager = ConfigurationManager()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            # Save config to file
            manager.save_config(config, temp_path)
            
            # Load config from file
            loaded_config = manager.load_config(temp_path)
            
            # Verify equivalence
            assert loaded_config.default_level == config.default_level
            assert loaded_config.explanation_verbosity == config.explanation_verbosity
            assert loaded_config.visual_aids_enabled == config.visual_aids_enabled
            assert loaded_config.diagram_style == config.diagram_style
            assert loaded_config.color_scheme == config.color_scheme
            assert loaded_config.progress_tracking_enabled == config.progress_tracking_enabled
            assert loaded_config.save_progress_locally == config.save_progress_locally
            assert loaded_config.suggested_topics_count == config.suggested_topics_count
            assert loaded_config.max_examples_per_topic == config.max_examples_per_topic
            assert loaded_config.exercise_difficulty_progression == config.exercise_difficulty_progression
            assert loaded_config.readthedocs_project == config.readthedocs_project
            assert loaded_config.sphinx_theme == config.sphinx_theme
            assert loaded_config.enable_interactive_sessions == config.enable_interactive_sessions
            assert loaded_config.session_timeout_minutes == config.session_timeout_minutes
            assert loaded_config.max_hint_count == config.max_hint_count
            
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    @given(config=learning_config_strategy())
    def test_file_round_trip_property_yaml(self, config):
        """
        Property 8: Configuration Serialization Round-trip (File I/O YAML)
        
        For any valid configuration object, saving to file then loading 
        should produce an equivalent configuration object.
        
        Validates: Requirements 7.4
        """
        # Feature: fishertools-enhancements, Property 8: Configuration Serialization Round-trip
        
        manager = ConfigurationManager()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name
        
        try:
            # Save config to file
            manager.save_config(config, temp_path)
            
            # Load config from file
            loaded_config = manager.load_config(temp_path)
            
            # Verify equivalence
            assert loaded_config.default_level == config.default_level
            assert loaded_config.explanation_verbosity == config.explanation_verbosity
            assert loaded_config.visual_aids_enabled == config.visual_aids_enabled
            assert loaded_config.diagram_style == config.diagram_style
            assert loaded_config.color_scheme == config.color_scheme
            assert loaded_config.progress_tracking_enabled == config.progress_tracking_enabled
            assert loaded_config.save_progress_locally == config.save_progress_locally
            assert loaded_config.suggested_topics_count == config.suggested_topics_count
            assert loaded_config.max_examples_per_topic == config.max_examples_per_topic
            assert loaded_config.exercise_difficulty_progression == config.exercise_difficulty_progression
            assert loaded_config.readthedocs_project == config.readthedocs_project
            assert loaded_config.sphinx_theme == config.sphinx_theme
            assert loaded_config.enable_interactive_sessions == config.enable_interactive_sessions
            assert loaded_config.session_timeout_minutes == config.session_timeout_minutes
            assert loaded_config.max_hint_count == config.max_hint_count
            
        except ValueError as e:
            if "YAML support not available" in str(e):
                pytest.skip("YAML support not available")
            else:
                raise
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestConfigurationParsingRobustness:
    """Property tests for configuration parsing robustness."""
    
    @given(config_dict=valid_config_dict_strategy())
    def test_valid_config_parsing_property(self, config_dict):
        """
        Property 7: Configuration Parsing Robustness (Valid Configs)
        
        For any valid configuration dictionary, the parser should successfully
        parse it and validation should pass.
        
        Validates: Requirements 7.1, 7.2, 7.5
        """
        # Feature: fishertools-enhancements, Property 7: Configuration Parsing Robustness
        
        parser = ConfigurationParser()
        manager = ConfigurationManager()
        
        # Validation should pass for valid configs
        validation_result = parser.validate_structure(config_dict)
        assert validation_result.is_valid, f"Valid config failed validation: {validation_result.errors}"
        
        # Should be able to convert to LearningConfig without errors
        learning_config = manager._dict_to_config(config_dict)
        assert isinstance(learning_config, LearningConfig)
        
        # JSON serialization should work
        json_content = parser.format_to_json(learning_config)
        assert isinstance(json_content, str)
        assert len(json_content) > 0
        
        # JSON parsing should work
        parsed_dict = parser.parse_json(json_content)
        assert isinstance(parsed_dict, dict)
    
    @given(config_dict=invalid_config_dict_strategy())
    def test_invalid_config_parsing_property(self, config_dict):
        """
        Property 7: Configuration Parsing Robustness (Invalid Configs)
        
        For any invalid configuration dictionary, the parser should detect
        validation errors and provide descriptive error messages.
        
        Validates: Requirements 7.1, 7.2, 7.5
        """
        # Feature: fishertools-enhancements, Property 7: Configuration Parsing Robustness
        
        parser = ConfigurationParser()
        
        # Validation should fail for invalid configs
        validation_result = parser.validate_structure(config_dict)
        
        # Should have validation errors
        assert not validation_result.is_valid or len(validation_result.errors) > 0
        
        # Error messages should be descriptive
        for error in validation_result.errors:
            assert isinstance(error.message, str)
            assert len(error.message) > 0
            assert isinstance(error.field_path, str)
            assert len(error.field_path) > 0
    
    def test_malformed_json_parsing_property(self):
        """
        Property 7: Configuration Parsing Robustness (Malformed JSON)
        
        For any malformed JSON string, the parser should raise a ValueError
        with a descriptive error message.
        
        Validates: Requirements 7.1, 7.2, 7.5
        """
        # Feature: fishertools-enhancements, Property 7: Configuration Parsing Robustness
        
        parser = ConfigurationParser()
        
        # Test with known malformed JSON strings
        malformed_examples = [
            '{"key": value}',  # Missing quotes around value
            '{"key": "value",}',  # Trailing comma
            '{key: "value"}',  # Missing quotes around key
            '{"key": "value"',  # Missing closing brace
            '{"key": "value"}}',  # Extra closing brace
            '{"key": "value" "key2": "value2"}',  # Missing comma
        ]
        
        for malformed_json in malformed_examples:
            # Should raise ValueError for malformed JSON
            with pytest.raises(ValueError) as exc_info:
                parser.parse_json(malformed_json)
            
            # Error message should be descriptive
            error_message = str(exc_info.value)
            assert "Invalid JSON configuration" in error_message
            assert len(error_message) > 0
    
    @given(config_dict=valid_config_dict_strategy())
    def test_config_change_application_property(self, config_dict):
        """
        Property 7: Configuration Parsing Robustness (Dynamic Changes)
        
        For any valid configuration, the system should be able to apply
        configuration changes dynamically without errors.
        
        Validates: Requirements 7.5
        """
        # Feature: fishertools-enhancements, Property 7: Configuration Parsing Robustness
        
        manager = ConfigurationManager()
        
        # Create LearningConfig from dict
        learning_config = manager._dict_to_config(config_dict)
        
        # Should be able to apply configuration without errors
        manager.apply_config(learning_config)
        
        # Should be able to retrieve current config
        current_config = manager.get_current_config()
        assert current_config is not None
        assert isinstance(current_config, LearningConfig)
        
        # Current config should match applied config
        assert current_config.default_level == learning_config.default_level
        assert current_config.explanation_verbosity == learning_config.explanation_verbosity