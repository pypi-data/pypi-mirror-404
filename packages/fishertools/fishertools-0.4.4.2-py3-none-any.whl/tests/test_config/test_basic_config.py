"""
Basic configuration tests to verify the setup works.
"""

import json
import pytest
from fishertools.config.models import LearningConfig


class TestBasicConfiguration:
    """Test basic configuration functionality."""
    
    def test_default_config_creation(self):
        """Test that default configuration can be created."""
        config = LearningConfig()
        
        # Verify default values
        assert config.default_level == "beginner"
        assert config.explanation_verbosity == "detailed"
        assert config.visual_aids_enabled is True
        assert config.progress_tracking_enabled is True
        assert config.suggested_topics_count == 3
        assert config.max_examples_per_topic == 5
        assert config.exercise_difficulty_progression == ["beginner", "intermediate", "advanced"]
    
    def test_config_with_custom_values(self):
        """Test configuration with custom values."""
        config = LearningConfig(
            default_level="intermediate",
            explanation_verbosity="brief",
            visual_aids_enabled=False,
            suggested_topics_count=5
        )
        
        assert config.default_level == "intermediate"
        assert config.explanation_verbosity == "brief"
        assert config.visual_aids_enabled is False
        assert config.suggested_topics_count == 5
    
    def test_default_config_file_exists(self):
        """Test that default configuration file exists and is valid JSON."""
        import os
        from fishertools.config import ConfigurationManager
        
        # Check if default config file exists
        config_path = "fishertools/config/default_config.json"
        assert os.path.exists(config_path), "Default configuration file should exist"
        
        # Verify it's valid JSON
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        # Verify required fields exist
        assert "default_level" in config_data
        assert "explanation_verbosity" in config_data
        assert "visual_aids_enabled" in config_data
        assert "progress_tracking_enabled" in config_data