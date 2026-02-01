"""
Configuration file parser supporting multiple formats.
"""

import json
import os
from typing import Dict, Any, Optional
from dataclasses import asdict
from .models import LearningConfig, ValidationResult, ConfigError, ErrorSeverity, ConfigFormat

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


class ConfigurationParser:
    """
    Parses configuration files in various formats with validation.
    
    Supports JSON, YAML, and TOML formats with comprehensive
    error reporting and validation.
    """
    
    def __init__(self):
        """Initialize the configuration parser."""
        pass
    
    def parse_file(self, config_path: str) -> Dict[str, Any]:
        """
        Parse a configuration file based on its extension.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Dict[str, Any]: Parsed configuration data
            
        Raises:
            ValueError: If file format is unsupported
            FileNotFoundError: If file doesn't exist
        """
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        format_type = self.detect_format(config_path)
        
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if format_type == ConfigFormat.JSON:
            return self.parse_json(content)
        elif format_type == ConfigFormat.YAML:
            return self.parse_yaml(content)
        else:
            raise ValueError(f"Unsupported configuration format: {format_type}")
    
    def parse_json(self, content: str) -> Dict[str, Any]:
        """
        Parse JSON configuration content.
        
        Args:
            content: JSON content to parse
            
        Returns:
            Dict[str, Any]: Parsed configuration data
            
        Raises:
            ValueError: If JSON is invalid
        """
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON configuration: {e}")
    
    def parse_yaml(self, content: str) -> Dict[str, Any]:
        """
        Parse YAML configuration content.
        
        Args:
            content: YAML content to parse
            
        Returns:
            Dict[str, Any]: Parsed configuration data
            
        Raises:
            ValueError: If YAML is invalid
        """
        if not YAML_AVAILABLE:
            raise ValueError("YAML support not available. Install PyYAML to use YAML configurations.")
        
        try:
            return yaml.safe_load(content) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML configuration: {e}")
    
    def format_to_json(self, config: LearningConfig) -> str:
        """
        Format configuration as JSON string.
        
        Args:
            config: Configuration to format
            
        Returns:
            str: JSON formatted configuration
        """
        config_dict = asdict(config)
        return json.dumps(config_dict, indent=2, ensure_ascii=False)
    
    def format_to_yaml(self, config: LearningConfig) -> str:
        """
        Format configuration as YAML string.
        
        Args:
            config: Configuration to format
            
        Returns:
            str: YAML formatted configuration
        """
        if not YAML_AVAILABLE:
            raise ValueError("YAML support not available. Install PyYAML to use YAML configurations.")
        
        config_dict = asdict(config)
        return yaml.dump(config_dict, default_flow_style=False, allow_unicode=True, indent=2)
    
    def validate_structure(self, config_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate configuration structure and types.
        
        Args:
            config_data: Configuration data to validate
            
        Returns:
            ValidationResult: Validation result with errors/warnings
        """
        errors = []
        warnings = []
        
        # Check required fields
        errors.extend(self._validate_required_fields(config_data))
        # Check field types and values
        field_errors = self._validate_field_types_and_values(config_data)
        errors.extend(field_errors)
        
        # Check for unknown fields
        warnings.extend(self._validate_unknown_fields(config_data))
        # Validate numeric ranges
        warnings.extend(self._validate_numeric_ranges(config_data))
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def _get_expected_fields(self) -> Dict[str, Any]:
        """Get expected fields and their types."""
        return {
            'default_level': str,
            'explanation_verbosity': str,
            'visual_aids_enabled': bool,
            'diagram_style': str,
            'color_scheme': str,
            'progress_tracking_enabled': bool,
            'save_progress_locally': bool,
            'suggested_topics_count': int,
            'max_examples_per_topic': int,
            'exercise_difficulty_progression': list,
            'readthedocs_project': (str, type(None)),
            'sphinx_theme': str,
            'enable_interactive_sessions': bool,
            'session_timeout_minutes': int,
            'max_hint_count': int
        }
    
    def _get_valid_values(self) -> Dict[str, list]:
        """Get valid values for enum-like fields."""
        return {
            'default_level': ['beginner', 'intermediate', 'advanced'],
            'explanation_verbosity': ['brief', 'detailed', 'comprehensive']
        }
    
    def _validate_required_fields(self, config_data: Dict[str, Any]) -> list:
        """Validate required fields are present."""
        errors = []
        required_fields = ['default_level', 'explanation_verbosity']
        
        for field in required_fields:
            if field not in config_data:
                errors.append(ConfigError(
                    message=f"Required field '{field}' is missing",
                    field_path=field,
                    severity=ErrorSeverity.ERROR,
                    suggested_fix=f"Add '{field}' field with a valid value"
                ))
        
        return errors
    
    def _validate_field_types_and_values(self, config_data: Dict[str, Any]) -> list:
        """Validate field types and enum values."""
        errors = []
        expected_fields = self._get_expected_fields()
        valid_values = self._get_valid_values()
        
        for field, expected_type in expected_fields.items():
            if field not in config_data:
                continue
                
            value = config_data[field]
            
            # Validate type
            type_error = self._validate_field_type(field, value, expected_type)
            if type_error:
                errors.append(type_error)
            
            # Validate enum values
            if field in valid_values and value not in valid_values[field]:
                errors.append(ConfigError(
                    message=f"Field '{field}' has invalid value '{value}'. Valid values: {valid_values[field]}",
                    field_path=field,
                    severity=ErrorSeverity.ERROR,
                    suggested_fix=f"Set '{field}' to one of: {', '.join(valid_values[field])}"
                ))
        
        return errors
    
    def _validate_field_type(self, field: str, value: Any, expected_type: Any) -> Optional[ConfigError]:
        """Validate a single field's type."""
        if isinstance(expected_type, tuple):
            if value is not None and not isinstance(value, expected_type[0]):
                return ConfigError(
                    message=f"Field '{field}' has invalid type. Expected {expected_type[0].__name__} or None, got {type(value).__name__}",
                    field_path=field,
                    severity=ErrorSeverity.ERROR,
                    suggested_fix=f"Change '{field}' to a {expected_type[0].__name__} value or null"
                )
        else:
            if not isinstance(value, expected_type):
                return ConfigError(
                    message=f"Field '{field}' has invalid type. Expected {expected_type.__name__}, got {type(value).__name__}",
                    field_path=field,
                    severity=ErrorSeverity.ERROR,
                    suggested_fix=f"Change '{field}' to a {expected_type.__name__} value"
                )
        return None
    
    def _validate_unknown_fields(self, config_data: Dict[str, Any]) -> list:
        """Check for unknown fields."""
        warnings = []
        expected_fields = self._get_expected_fields()
        
        for field in config_data:
            if field not in expected_fields:
                warnings.append(ConfigError(
                    message=f"Unknown field '{field}' will be ignored",
                    field_path=field,
                    severity=ErrorSeverity.WARNING,
                    suggested_fix=f"Remove '{field}' field or check for typos"
                ))
        
        return warnings
    
    def _validate_numeric_ranges(self, config_data: Dict[str, Any]) -> list:
        """Validate numeric field ranges."""
        warnings = []
        
        # Validate suggested_topics_count
        if 'suggested_topics_count' in config_data:
            value = config_data['suggested_topics_count']
            if isinstance(value, int) and (value < 1 or value > 10):
                warnings.append(ConfigError(
                    message=f"Field 'suggested_topics_count' value {value} is outside recommended range (1-10)",
                    field_path='suggested_topics_count',
                    severity=ErrorSeverity.WARNING,
                    suggested_fix="Set 'suggested_topics_count' to a value between 1 and 10"
                ))
        
        # Validate max_examples_per_topic
        if 'max_examples_per_topic' in config_data:
            value = config_data['max_examples_per_topic']
            if isinstance(value, int) and (value < 1 or value > 20):
                warnings.append(ConfigError(
                    message=f"Field 'max_examples_per_topic' value {value} is outside recommended range (1-20)",
                    field_path='max_examples_per_topic',
                    severity=ErrorSeverity.WARNING,
                    suggested_fix="Set 'max_examples_per_topic' to a value between 1 and 20"
                ))
        
        return warnings
    
    def detect_format(self, file_path: str) -> ConfigFormat:
        """
        Detect configuration file format from extension.
        
        Args:
            file_path: Path to the configuration file
            
        Returns:
            ConfigFormat: Detected file format
        """
        _, ext = os.path.splitext(file_path.lower())
        
        if ext == '.json':
            return ConfigFormat.JSON
        elif ext in ['.yaml', '.yml']:
            return ConfigFormat.YAML
        elif ext == '.toml':
            return ConfigFormat.TOML
        else:
            # Default to JSON if extension is unknown
            return ConfigFormat.JSON