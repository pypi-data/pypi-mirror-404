"""
Integration layer for fishertools enhancement components.

This module provides the main integration point that connects all enhancement
components: Learning System, Documentation Generator, Example Repository,
Visual Documentation, and Configuration Manager.
"""

from typing import Optional, Dict, Any, List
import logging
from pathlib import Path

# Import all enhancement components
from .learning import LearningSystem, TutorialEngine, ProgressSystem, InteractiveSessionManager
from .documentation import DocumentationGenerator, VisualDocumentation, APIGenerator
from .examples import ExampleRepository
from .config import ConfigurationManager, LearningConfig
from .errors import FishertoolsError, get_recovery_manager, with_error_recovery


class FishertoolsIntegration:
    """
    Main integration class that coordinates all fishertools enhancement components.
    
    This class serves as the central hub for all learning, documentation, and
    example management functionality. It handles component initialization,
    configuration management, and inter-component communication.
    """
    
    def __init__(self, config_path: Optional[str] = None, project_name: str = "fishertools"):
        """
        Initialize the fishertools integration system.
        
        Args:
            config_path: Optional path to configuration file
            project_name: Name of the project for documentation
        """
        self.project_name = project_name
        self.config_path = config_path
        
        # Initialize error recovery manager
        self.recovery_manager = get_recovery_manager()
        
        # Initialize configuration manager first
        self.config_manager = ConfigurationManager(config_path)
        
        # Load configuration
        try:
            if config_path and Path(config_path).exists():
                self.config = self.config_manager.load_config(config_path)
            else:
                self.config = self.config_manager.get_default_config()
        except Exception as e:
            logging.warning(f"Failed to load configuration: {e}. Using defaults.")
            self.config = self.config_manager.get_default_config()
        
        # Initialize core components
        self._initialize_components()
        
        # Set up component integrations
        self._setup_integrations()
    
    def _initialize_components(self) -> None:
        """Initialize all enhancement components."""
        try:
            # Learning System components
            self.learning_system = LearningSystem(self.config_path)
            self.tutorial_engine = TutorialEngine()
            self.progress_system = ProgressSystem()
            self.session_manager = InteractiveSessionManager()
            
            # Documentation components
            self.doc_generator = DocumentationGenerator(
                project_name=self.project_name,
                output_dir=getattr(self.config, 'docs_output_dir', 'docs')
            )
            self.visual_docs = VisualDocumentation()
            self.api_generator = APIGenerator()
            
            # Example management
            self.example_repository = ExampleRepository()
            
            logging.info("All fishertools components initialized successfully")
            
        except Exception as e:
            # Use error recovery for component initialization failures
            recovery_action = self.recovery_manager.handle_config_error(e, "integration")
            
            if recovery_action.strategy.value == "graceful_degradation":
                # Initialize with minimal components
                self._initialize_minimal_components()
                logging.warning("Initialized with minimal components due to errors")
            else:
                logging.error(f"Failed to initialize components: {e}")
                raise FishertoolsError(f"Component initialization failed: {e}")
    
    def _initialize_minimal_components(self) -> None:
        """Initialize minimal components for graceful degradation."""
        try:
            # Only initialize essential components
            self.learning_system = LearningSystem()
            self.example_repository = ExampleRepository()
            
            # Set others to None for graceful handling
            self.tutorial_engine = None
            self.progress_system = None
            self.session_manager = None
            self.doc_generator = None
            self.visual_docs = None
            self.api_generator = None
            
        except Exception as e:
            logging.critical(f"Failed to initialize even minimal components: {e}")
            raise FishertoolsError(f"Critical initialization failure: {e}")
    
    def _setup_integrations(self) -> None:
        """Set up integrations between components."""
        try:
            # Connect Learning System with Tutorial Engine
            self.learning_system._tutorial_engine = self.tutorial_engine
            self.learning_system._progress_system = self.progress_system
            self.learning_system._session_manager = self.session_manager
            
            # Connect Tutorial Engine with Example Repository
            self.tutorial_engine._example_repository = self.example_repository
            
            # Connect Documentation Generator with Visual Documentation
            self.doc_generator._visual_docs = self.visual_docs
            
            # Connect Session Manager with Example Repository
            self.session_manager._example_repository = self.example_repository
            self.session_manager._tutorial_engine = self.tutorial_engine
            
            logging.info("Component integrations set up successfully")
            
        except Exception as e:
            logging.error(f"Failed to set up integrations: {e}")
            raise FishertoolsError(f"Integration setup failed: {e}")
    
    @with_error_recovery("integration", "start_learning_session", "session_error")
    def start_learning_session(self, topic: str, level: str = "beginner", user_id: Optional[str] = None):
        """
        Start a comprehensive learning session that integrates all components.
        
        Args:
            topic: Topic to learn
            level: Difficulty level
            user_id: Optional user identifier for progress tracking
            
        Returns:
            Integrated learning session with examples, tutorials, and progress tracking
        """
        try:
            # Start tutorial session
            tutorial_session = self.learning_system.start_tutorial(topic, level)
            
            # Get relevant examples from repository if available
            if self.example_repository:
                examples = self.example_repository.get_examples_by_topic(topic)
                
                # Create interactive session if examples are available and session manager exists
                if examples and self.session_manager:
                    interactive_session = self.session_manager.create_session(
                        user_id or "anonymous",
                        examples[0]  # Start with first example
                    )
                    tutorial_session.interactive_session = interactive_session
            
            # Track progress if user_id provided and progress system available
            if user_id and self.progress_system:
                self.learning_system.track_progress(user_id, topic, False)  # Mark as started
            
            return tutorial_session
            
        except Exception as e:
            # Graceful degradation - provide basic tutorial without interactive features
            logging.warning(f"Failed to create full learning session: {e}")
            
            if self.learning_system:
                try:
                    return self.learning_system.start_tutorial(topic, level)
                except Exception as basic_error:
                    logging.error(f"Failed to start even basic tutorial: {basic_error}")
                    raise FishertoolsError(f"Learning session failed: {basic_error}")
            else:
                raise FishertoolsError(f"Learning system unavailable: {e}")
    
    @with_error_recovery("integration", "generate_documentation", "documentation_error")
    def generate_comprehensive_documentation(self, module_paths: List[str]) -> Dict[str, Any]:
        """
        Generate comprehensive documentation with visual elements.
        
        Args:
            module_paths: List of module paths to document
            
        Returns:
            Dictionary containing all generated documentation artifacts
        """
        try:
            # Generate API documentation
            sphinx_docs = self.doc_generator.build_documentation(module_paths)
            
            # Generate visual documentation for each module
            visual_artifacts = {}
            for module_path in module_paths:
                api_info = self.doc_generator.extract_api_info(module_path)
                
                # Create architecture diagram
                arch_diagram = self.visual_docs.create_architecture_diagram([api_info.module_name])
                visual_artifacts[f"{api_info.module_name}_architecture"] = arch_diagram
                
                # Create data flow diagrams for functions
                for func_info in api_info.functions:
                    flow_diagram = self.visual_docs.generate_data_flow_diagram(func_info)
                    visual_artifacts[f"{func_info.name}_flow"] = flow_diagram
            
            # Publish to ReadTheDocs
            publish_result = self.doc_generator.publish_to_readthedocs(sphinx_docs)
            
            return {
                'sphinx_docs': sphinx_docs,
                'visual_artifacts': visual_artifacts,
                'publish_result': publish_result
            }
            
        except Exception as e:
            logging.error(f"Failed to generate documentation: {e}")
            raise FishertoolsError(f"Documentation generation failed: {e}")
    
    def get_learning_recommendations(self, user_id: str, current_topic: Optional[str] = None) -> Dict[str, Any]:
        """
        Get personalized learning recommendations based on user progress.
        
        Args:
            user_id: User identifier
            current_topic: Optional current topic being studied
            
        Returns:
            Dictionary with recommendations including next topics, examples, and exercises
        """
        try:
            # Get user progress
            progress = self.learning_system.get_user_progress(user_id)
            
            recommendations = {
                'next_topics': [],
                'recommended_examples': [],
                'suggested_exercises': [],
                'progress_summary': None
            }
            
            if progress:
                recommendations['progress_summary'] = {
                    'completed_topics': progress.completed_topics,
                    'current_level': progress.current_level.value,
                    'total_exercises': progress.total_exercises_completed
                }
                
                # Get next topic recommendations
                if current_topic:
                    related_topics = self.learning_system.suggest_related_topics(current_topic)
                    # Filter out already completed topics
                    next_topics = [
                        topic for topic in related_topics 
                        if topic not in progress.completed_topics
                    ]
                    recommendations['next_topics'] = next_topics[:3]  # Top 3 recommendations
                
                # Get examples for recommended topics
                for topic in recommendations['next_topics']:
                    examples = self.example_repository.get_examples_by_topic(topic)
                    recommendations['recommended_examples'].extend(examples[:2])  # 2 per topic
            
            return recommendations
            
        except Exception as e:
            logging.error(f"Failed to get recommendations: {e}")
            return {
                'next_topics': [],
                'recommended_examples': [],
                'suggested_exercises': [],
                'progress_summary': None,
                'error': str(e)
            }
    
    def explain_code_with_examples(self, code: str, include_visuals: bool = True) -> Dict[str, Any]:
        """
        Provide comprehensive code explanation with examples and visual aids.
        
        Args:
            code: Code to explain
            include_visuals: Whether to include visual diagrams
            
        Returns:
            Dictionary with step-by-step explanation, related examples, and visual aids
        """
        try:
            # Get step-by-step explanation
            explanations = self.learning_system.get_step_by_step_explanation(code)
            
            # Find related examples based on concepts in the code
            related_examples = []
            concepts = set()
            for explanation in explanations:
                concepts.update(explanation.related_concepts)
            
            # Search for examples covering these concepts
            for concept in concepts:
                examples = self.example_repository.search_examples(concept)
                related_examples.extend(examples[:2])  # Limit to avoid overwhelming
            
            result = {
                'step_explanations': explanations,
                'related_examples': related_examples,
                'concepts_covered': list(concepts)
            }
            
            # Add visual aids if requested
            if include_visuals and explanations:
                try:
                    # Create a simple flowchart for the code structure
                    flowchart = self.visual_docs.create_algorithm_flowchart(code)
                    result['flowchart'] = flowchart
                except Exception as e:
                    logging.warning(f"Failed to create flowchart: {e}")
            
            return result
            
        except Exception as e:
            logging.error(f"Failed to explain code: {e}")
            raise FishertoolsError(f"Code explanation failed: {e}")
    
    def update_configuration(self, new_config: Dict[str, Any]) -> None:
        """
        Update system configuration and apply changes to all components.
        
        Args:
            new_config: New configuration values
        """
        try:
            # Merge with current configuration
            updated_config = self.config_manager.merge_configs(self.config, new_config)
            
            # Validate the new configuration
            validation_result = self.config_manager.validate_config(updated_config)
            if not validation_result.is_valid:
                error_messages = [error.message for error in validation_result.errors]
                raise ValueError(f"Invalid configuration: {'; '.join(error_messages)}")
            
            # Apply the configuration
            self.config_manager.apply_config(updated_config)
            self.config = updated_config
            
            # Update components with new configuration
            self._apply_config_to_components()
            
            logging.info("Configuration updated successfully")
            
        except Exception as e:
            logging.error(f"Failed to update configuration: {e}")
            raise FishertoolsError(f"Configuration update failed: {e}")
    
    def _apply_config_to_components(self) -> None:
        """Apply current configuration to all components."""
        try:
            # Apply configuration to learning system
            if hasattr(self.config, 'default_level'):
                # Update default difficulty level in learning system
                pass  # Implementation depends on specific config options
            
            # Apply configuration to documentation generator
            if hasattr(self.config, 'docs_output_dir'):
                self.doc_generator.output_dir = self.config.docs_output_dir
            
            # Apply other configuration options as needed
            
        except Exception as e:
            logging.warning(f"Some configuration options could not be applied: {e}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get the current status of all system components.
        
        Returns:
            Dictionary with status information for each component
        """
        status = {
            'learning_system': 'initialized' if self.learning_system else 'failed',
            'documentation_generator': 'initialized' if self.doc_generator else 'failed',
            'example_repository': 'initialized' if self.example_repository else 'failed',
            'visual_documentation': 'initialized' if self.visual_docs else 'failed',
            'configuration_manager': 'initialized' if self.config_manager else 'failed',
            'current_config': self.config.__dict__ if self.config else None,
            'total_examples': len(self.example_repository._examples) if self.example_repository else 0
        }
        
        return status


# Global integration instance for easy access
_integration_instance: Optional[FishertoolsIntegration] = None


def get_integration(config_path: Optional[str] = None, project_name: str = "fishertools") -> FishertoolsIntegration:
    """
    Get or create the global fishertools integration instance.
    
    Args:
        config_path: Optional path to configuration file
        project_name: Name of the project
        
    Returns:
        FishertoolsIntegration: The global integration instance
    """
    global _integration_instance
    
    if _integration_instance is None:
        _integration_instance = FishertoolsIntegration(config_path, project_name)
    
    return _integration_instance


def reset_integration() -> None:
    """Reset the global integration instance."""
    global _integration_instance
    _integration_instance = None


# Convenience functions for common operations
def start_learning(topic: str, level: str = "beginner", user_id: Optional[str] = None):
    """Convenience function to start a learning session."""
    integration = get_integration()
    return integration.start_learning_session(topic, level, user_id)


def explain_code(code: str, include_visuals: bool = True):
    """Convenience function to explain code with examples."""
    integration = get_integration()
    return integration.explain_code_with_examples(code, include_visuals)


def generate_docs(module_paths: List[str]):
    """Convenience function to generate comprehensive documentation."""
    integration = get_integration()
    return integration.generate_comprehensive_documentation(module_paths)


def get_recommendations(user_id: str, current_topic: Optional[str] = None):
    """Convenience function to get learning recommendations."""
    integration = get_integration()
    return integration.get_learning_recommendations(user_id, current_topic)