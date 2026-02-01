"""
Configuration manager for the learning system.
"""

from typing import Optional, Dict, Any
import json
import os
from dataclasses import asdict
from .models import LearningConfig, ValidationResult, RecoveryAction, ConfigError
from .parser import ConfigurationParser


class ConfigurationManager:
    """
    Manages learning system configuration through various file formats.
    
    Handles loading, saving, validation, and error recovery for
    configuration files in JSON, YAML, and TOML formats.
    """
    
    def __init__(self, default_config_path: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            default_config_path: Optional path to default configuration file
        """
        self.default_config_path = default_config_path or self._get_default_config_path()
        self.parser = ConfigurationParser()
        self._current_config: Optional[LearningConfig] = None
    
    def _get_default_config_path(self) -> str:
        """Get the path to the default configuration file."""
        current_dir = os.path.dirname(__file__)
        return os.path.join(current_dir, 'default_config.json')
    
    def load_config(self, config_path: str) -> LearningConfig:
        """
        Load configuration from a file.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            LearningConfig: Loaded configuration
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config format is invalid
        """
        try:
            # Parse the configuration file
            config_data = self.parser.parse_file(config_path)
            
            # Validate the configuration
            validation_result = self.parser.validate_structure(config_data)
            
            if not validation_result.is_valid:
                error_messages = [error.message for error in validation_result.errors]
                raise ValueError(f"Configuration validation failed: {'; '.join(error_messages)}")
            
            # Create LearningConfig object with defaults for missing fields
            default_config = self.get_default_config()
            merged_config = self.merge_configs(default_config, config_data)
            
            self._current_config = merged_config
            return merged_config
            
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        except Exception as e:
            raise ValueError(f"Failed to load configuration: {e}")
    
    def save_config(self, config: LearningConfig, config_path: str) -> None:
        """
        Save configuration to a file.
        
        Args:
            config: Configuration to save
            config_path: Path where to save the configuration
            
        Raises:
            IOError: If file cannot be written
        """
        try:
            # Determine format based on file extension
            format_type = self.parser.detect_format(config_path)
            
            # Format the configuration
            if format_type.value == 'json':
                content = self.parser.format_to_json(config)
            elif format_type.value == 'yaml':
                content = self.parser.format_to_yaml(config)
            else:
                raise ValueError(f"Unsupported format for saving: {format_type}")
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            # Write the file
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
        except Exception as e:
            raise IOError(f"Failed to save configuration to {config_path}: {e}")
    
    def validate_config(self, config: LearningConfig) -> ValidationResult:
        """
        Validate a configuration object.
        
        Args:
            config: Configuration to validate
            
        Returns:
            ValidationResult: Validation result with errors/warnings
        """
        # Convert config to dict for validation
        config_dict = asdict(config)
        return self.parser.validate_structure(config_dict)
    
    def apply_config(self, config: LearningConfig) -> None:
        """
        Apply configuration to the learning system.
        
        Args:
            config: Configuration to apply
        """
        # Validate the configuration first
        validation_result = self.validate_config(config)
        
        if not validation_result.is_valid:
            error_messages = [error.message for error in validation_result.errors]
            raise ValueError(f"Cannot apply invalid configuration: {'; '.join(error_messages)}")
        
        # Store as current configuration
        self._current_config = config
        
        # Here we would apply the configuration to various system components
        # For now, we just store it as the current configuration
    
    def get_default_config(self) -> LearningConfig:
        """
        Get the default configuration.
        
        Returns:
            LearningConfig: Default configuration
        """
        try:
            if os.path.exists(self.default_config_path):
                config_data = self.parser.parse_file(self.default_config_path)
                return self._dict_to_config(config_data)
            else:
                # Return hardcoded defaults if file doesn't exist
                return LearningConfig()
        except Exception:
            # Return hardcoded defaults if parsing fails
            return LearningConfig()
    
    def merge_configs(self, base_config: LearningConfig, override_config: Dict[str, Any]) -> LearningConfig:
        """
        Merge configuration with overrides.
        
        Args:
            base_config: Base configuration
            override_config: Configuration overrides
            
        Returns:
            LearningConfig: Merged configuration
        """
        # Convert base config to dict
        base_dict = asdict(base_config)
        
        # Update with overrides
        base_dict.update(override_config)
        
        # Convert back to LearningConfig
        return self._dict_to_config(base_dict)
    
    def _dict_to_config(self, config_dict: Dict[str, Any]) -> LearningConfig:
        """
        Convert dictionary to LearningConfig object.
        
        Args:
            config_dict: Configuration dictionary
            
        Returns:
            LearningConfig: Configuration object
        """
        # Filter out unknown fields and create LearningConfig
        valid_fields = {
            field.name for field in LearningConfig.__dataclass_fields__.values()
        }
        
        filtered_dict = {
            key: value for key, value in config_dict.items()
            if key in valid_fields
        }
        
        return LearningConfig(**filtered_dict)
    
    def get_current_config(self) -> Optional[LearningConfig]:
        """
        Get the currently loaded configuration.
        
        Returns:
            Optional[LearningConfig]: Current configuration or None if not loaded
        """
        return self._current_config
    
    def handle_config_error(self, error: ConfigError) -> RecoveryAction:
        """
        Handle configuration errors with appropriate recovery actions.
        
        Args:
            error: Configuration error to handle
            
        Returns:
            RecoveryAction: Recommended recovery action
        """
        from ..errors.recovery import get_recovery_manager, ErrorContext, ErrorSeverity
        
        recovery_manager = get_recovery_manager()
        
        # Determine error severity based on error type
        if isinstance(error, FileNotFoundError):
            severity = ErrorSeverity.MEDIUM
            error_type = "config_file_missing"
        elif "validation" in str(error).lower():
            severity = ErrorSeverity.MEDIUM
            error_type = "config_validation_error"
        elif "parse" in str(error).lower() or "syntax" in str(error).lower():
            severity = ErrorSeverity.HIGH
            error_type = "config_parse_error"
        else:
            severity = ErrorSeverity.MEDIUM
            error_type = "config_general_error"
        
        error_context = ErrorContext(
            component="configuration",
            operation="load_config",
            error_type=error_type,
            error_message=str(error),
            severity=severity,
            metadata={"config_path": getattr(error, 'config_path', 'unknown')}
        )
        
        return recovery_manager.handle_error(error_context)