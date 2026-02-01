"""
Core Learning System implementation.
"""

import ast
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Set
from .models import (
    TutorialSession, StepExplanation, DifficultyLevel, 
    CodeContext, LearningProgress, InteractiveExercise, ExerciseStatus
)


class LearningSystem:
    """
    Central component coordinating all learning activities.
    
    Provides step-by-step explanations, tutorial management,
    and progress tracking for Python beginners.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the learning system with optional configuration."""
        self.config_path = config_path
        self._tutorial_engine = None
        self._progress_system = None
        self._session_manager = None
        
        # Topic relationships for suggesting related topics
        self._topic_relationships = {
            "variables": ["data_types", "operators", "input_output"],
            "data_types": ["variables", "type_conversion", "strings"],
            "lists": ["loops", "indexing", "list_methods", "collections"],
            "dictionaries": ["lists", "collections", "key_value_pairs"],
            "loops": ["lists", "conditionals", "iteration"],
            "functions": ["parameters", "return_values", "scope"],
            "conditionals": ["boolean_logic", "comparison_operators"],
            "error_handling": ["exceptions", "try_except", "debugging"],
            "file_operations": ["strings", "error_handling", "paths"],
            "classes": ["objects", "methods", "inheritance"],
            "modules": ["imports", "packages", "namespaces"]
        }
        
        # Content adaptation templates by level
        self._level_adaptations = {
            DifficultyLevel.BEGINNER: {
                "vocabulary": "simple",
                "examples": "basic",
                "detail_level": "high",
                "prerequisites": "minimal"
            },
            DifficultyLevel.INTERMEDIATE: {
                "vocabulary": "technical",
                "examples": "practical",
                "detail_level": "medium",
                "prerequisites": "some"
            },
            DifficultyLevel.ADVANCED: {
                "vocabulary": "advanced",
                "examples": "complex",
                "detail_level": "low",
                "prerequisites": "extensive"
            }
        }
    
    def start_tutorial(self, topic: str, level: str = "beginner") -> TutorialSession:
        """
        Start a new tutorial session for the given topic and level.
        
        Args:
            topic: The topic to learn (e.g., "lists", "functions", "error_handling")
            level: Difficulty level ("beginner", "intermediate", "advanced")
            
        Returns:
            TutorialSession: A new tutorial session object
            
        Raises:
            ValueError: If topic or level is invalid
        """
        # Validate level
        try:
            difficulty_level = DifficultyLevel(level)
        except ValueError:
            raise ValueError(f"Invalid level '{level}'. Must be one of: beginner, intermediate, advanced")
        
        # Validate topic (basic validation - could be expanded)
        if not topic or not isinstance(topic, str):
            raise ValueError("Topic must be a non-empty string")
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Create basic exercises for the topic (simplified for now)
        exercises = self._create_exercises_for_topic(topic, difficulty_level)
        
        # Create tutorial session
        session = TutorialSession(
            session_id=session_id,
            topic=topic,
            level=difficulty_level,
            start_time=datetime.now(),
            exercises=exercises
        )
        
        return session
    
    def get_step_by_step_explanation(self, code: str, context: Optional[CodeContext] = None) -> List[StepExplanation]:
        """
        Generate step-by-step explanation for the given code.
        
        Args:
            code: Python code to explain
            context: Optional context information for better explanations
            
        Returns:
            List[StepExplanation]: Detailed explanations for each step
        """
        if not code or not isinstance(code, str):
            raise ValueError("Code must be a non-empty string")
        
        explanations = []
        
        try:
            # Parse the code into an AST
            tree = ast.parse(code.strip())
            
            # Generate explanations for each statement
            for i, node in enumerate(ast.walk(tree)):
                if isinstance(node, (ast.stmt, ast.expr)):
                    explanation = self._explain_ast_node(node, i + 1, context)
                    if explanation:
                        explanations.append(explanation)
                        
        except SyntaxError as e:
            # If code has syntax errors, provide a basic explanation
            explanations.append(StepExplanation(
                step_number=1,
                description=f"Syntax error in code: {str(e)}",
                code_snippet=code,
                related_concepts=["syntax", "debugging"]
            ))
        
        return explanations
    
    def suggest_related_topics(self, current_topic: str) -> List[str]:
        """
        Suggest related topics based on the current topic.
        
        Args:
            current_topic: The topic currently being studied
            
        Returns:
            List[str]: List of related topic names
        """
        if not current_topic or not isinstance(current_topic, str):
            return []
        
        # Get direct relationships
        related = self._topic_relationships.get(current_topic.lower(), [])
        
        # Add topics that reference the current topic
        for topic, relationships in self._topic_relationships.items():
            if current_topic.lower() in relationships and topic not in related:
                related.append(topic)
        
        return related[:5]  # Limit to 5 suggestions
    
    def adapt_content_for_level(self, content: str, level: str) -> str:
        """
        Adapt content complexity for the specified level.
        
        Args:
            content: Original content to adapt
            level: Target difficulty level
            
        Returns:
            str: Adapted content appropriate for the level
        """
        if not content or not isinstance(content, str):
            return content
        
        try:
            difficulty_level = DifficultyLevel(level)
        except ValueError:
            return content  # Return original if invalid level
        
        adaptation = self._level_adaptations[difficulty_level]
        
        # Apply adaptations based on level
        if difficulty_level == DifficultyLevel.BEGINNER:
            # Add more explanatory text and simpler vocabulary
            adapted = self._simplify_vocabulary(content)
            adapted = self._add_beginner_context(adapted)
        elif difficulty_level == DifficultyLevel.INTERMEDIATE:
            # Balance between detail and conciseness
            adapted = self._add_practical_context(content)
        else:  # ADVANCED
            # More concise, assume prior knowledge
            adapted = self._make_concise(content)
        
        return adapted
    
    def track_progress(self, user_id: str, topic: str, completed: bool) -> None:
        """
        Track user progress for a specific topic.
        
        Args:
            user_id: Unique identifier for the user
            topic: Topic that was studied
            completed: Whether the topic was completed successfully
        """
        if not self._progress_system:
            from .progress import ProgressSystem
            self._progress_system = ProgressSystem()
        
        self._progress_system.update_progress(user_id, topic, completed)
    
    def get_user_progress(self, user_id: str) -> Optional[LearningProgress]:
        """
        Get current progress for a user.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            Optional[LearningProgress]: User's progress or None if not found
        """
        if not self._progress_system:
            from .progress import ProgressSystem
            self._progress_system = ProgressSystem()
        
        return self._progress_system.get_progress(user_id)
    def _create_exercises_for_topic(self, topic: str, level: DifficultyLevel) -> List[InteractiveExercise]:
        """Create basic exercises for a given topic and level."""
        exercises = []
        
        # Basic exercise templates by topic
        exercise_templates = {
            "variables": {
                "title": "Working with Variables",
                "description": "Practice creating and using variables",
                "starter_code": "# Create a variable called 'name' and assign your name to it\n",
                "expected_output": "Variable assignment"
            },
            "lists": {
                "title": "List Operations",
                "description": "Practice creating and manipulating lists",
                "starter_code": "# Create a list of your favorite colors\ncolors = []\n",
                "expected_output": "List with items"
            },
            "functions": {
                "title": "Function Definition",
                "description": "Practice defining and calling functions",
                "starter_code": "# Define a function that greets a person\ndef greet(name):\n    pass\n",
                "expected_output": "Function definition"
            }
        }
        
        template = exercise_templates.get(topic.lower())
        if template:
            exercise = InteractiveExercise(
                id=str(uuid.uuid4()),
                title=template["title"],
                description=template["description"],
                starter_code=template["starter_code"],
                expected_output=template["expected_output"],
                hints=["Think about the basic syntax", "Check the examples"],
                difficulty_level=level,
                topic=topic
            )
            exercises.append(exercise)
        
        return exercises
    
    def _explain_ast_node(self, node: ast.AST, step_number: int, context: Optional[CodeContext]) -> Optional[StepExplanation]:
        """Generate explanation for an AST node."""
        if isinstance(node, ast.Assign):
            return StepExplanation(
                step_number=step_number,
                description="Variable assignment: storing a value in a variable",
                code_snippet=ast.unparse(node) if hasattr(ast, 'unparse') else str(node),
                related_concepts=["variables", "assignment"]
            )
        elif isinstance(node, ast.FunctionDef):
            return StepExplanation(
                step_number=step_number,
                description=f"Function definition: creating a reusable block of code named '{node.name}'",
                code_snippet=ast.unparse(node) if hasattr(ast, 'unparse') else str(node),
                related_concepts=["functions", "definition", "parameters"]
            )
        elif isinstance(node, ast.Call):
            return StepExplanation(
                step_number=step_number,
                description="Function call: executing a function with given arguments",
                code_snippet=ast.unparse(node) if hasattr(ast, 'unparse') else str(node),
                related_concepts=["functions", "calls", "arguments"]
            )
        elif isinstance(node, ast.If):
            return StepExplanation(
                step_number=step_number,
                description="Conditional statement: executing code based on a condition",
                code_snippet=ast.unparse(node) if hasattr(ast, 'unparse') else str(node),
                related_concepts=["conditionals", "boolean_logic"]
            )
        
        return None
    
    def _simplify_vocabulary(self, content: str) -> str:
        """Simplify vocabulary for beginners."""
        # Basic vocabulary replacements
        replacements = {
            "instantiate": "create",
            "initialize": "set up",
            "parameter": "input value",
            "argument": "value you pass in",
            "iterate": "go through each item",
            "concatenate": "join together"
        }
        
        result = content
        for technical, simple in replacements.items():
            result = result.replace(technical, simple)
        
        return result
    
    def _add_beginner_context(self, content: str) -> str:
        """Add extra context for beginners."""
        return f"For beginners: {content}\n\nRemember: Take your time and don't worry if this seems complex at first!"
    
    def _add_practical_context(self, content: str) -> str:
        """Add practical context for intermediate learners."""
        return f"{content}\n\nPractical tip: This concept is commonly used in real-world programming."
    
    def _make_concise(self, content: str) -> str:
        """Make content more concise for advanced learners."""
        # Remove beginner-specific phrases
        phrases_to_remove = [
            "For beginners: ",
            "Remember: ",
            "Don't worry if this seems complex",
            "Take your time"
        ]
        
        result = content
        for phrase in phrases_to_remove:
            result = result.replace(phrase, "")
        
        return result.strip()