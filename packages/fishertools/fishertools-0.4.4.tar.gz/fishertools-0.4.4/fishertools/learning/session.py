"""
Interactive session manager for learning activities.
"""

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from .models import (
    TutorialSession, InteractiveExercise, ValidationResult,
    DifficultyLevel, ExerciseStatus
)
from .tutorial import TutorialEngine


class InteractiveSessionManager:
    """
    Manages interactive learning sessions with exercises and feedback.
    
    Handles user input, provides feedback, and manages session state
    for interactive learning experiences.
    """
    
    def __init__(self):
        """Initialize the session manager."""
        self._active_sessions: Dict[str, TutorialSession] = {}
        self._tutorial_engine = TutorialEngine()
        
        # Integration points
        self._example_repository = None
        
        # Additional examples by topic for when users struggle
        self._additional_examples = {
            'variables': [
                "Try creating a variable for your favorite color: color = 'blue'",
                "Create a variable for a number: count = 42",
                "Make a variable for your city: city = 'New York'",
                "Store a boolean value: is_student = True"
            ],
            'lists': [
                "Create a list of numbers: numbers = [1, 2, 3, 4, 5]",
                "Make a list of names: friends = ['Alice', 'Bob', 'Charlie']",
                "Try an empty list first: empty_list = []",
                "Add items one by one: my_list.append('new_item')"
            ],
            'functions': [
                "Start with a simple function: def say_hello(): print('Hello!')",
                "Try a function with a parameter: def greet(name): print(f'Hi, {name}!')",
                "Create a function that returns a value: def add_numbers(a, b): return a + b",
                "Remember to call your function after defining it: say_hello()"
            ],
            'loops': [
                "Simple loop over a list: for item in [1, 2, 3]: print(item)",
                "Loop with range: for i in range(5): print(i)",
                "Loop over strings: for char in 'hello': print(char)",
                "Use meaningful variable names: for student in students: print(student)"
            ],
            'conditionals': [
                "Basic if statement: if age >= 18: print('Adult')",
                "If-else: if score > 90: print('A') else: print('Try again')",
                "Multiple conditions: if x > 0 and x < 10: print('Single digit')",
                "Check for equality: if name == 'Alice': print('Hello Alice!')"
            ]
        }
    
    def create_session(self, user_id: str, topic: str, level: DifficultyLevel) -> TutorialSession:
        """
        Create a new interactive learning session.
        
        Args:
            user_id: Unique identifier for the user
            topic: Topic for the session
            level: Difficulty level for the session
            
        Returns:
            TutorialSession: New tutorial session
        """
        if not user_id or not isinstance(user_id, str):
            raise ValueError("User ID must be a non-empty string")
        
        if not topic or not isinstance(topic, str):
            raise ValueError("Topic must be a non-empty string")
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Create exercises for the topic using the tutorial engine
        exercises = []
        
        # Create multiple exercises of increasing difficulty
        base_exercise = self._tutorial_engine.create_interactive_exercise(topic, level)
        exercises.append(base_exercise)
        
        # Add a follow-up exercise if beginner level
        if level == DifficultyLevel.BEGINNER:
            follow_up = self._create_follow_up_exercise(topic, level)
            if follow_up:
                exercises.append(follow_up)
        
        # Create the session
        session = TutorialSession(
            session_id=session_id,
            topic=topic,
            level=level,
            start_time=datetime.now(),
            exercises=exercises,
            current_exercise_index=0,
            is_completed=False
        )
        
        # Store the session
        self._active_sessions[session_id] = session
        
        return session
    
    def create_session_from_example(self, user_id: str, example):
        """
        Create a session based on a specific example from the repository.
        
        Args:
            user_id: Unique identifier for the user
            example: CodeExample from the repository
            
        Returns:
            TutorialSession: New tutorial session based on the example
        """
        if not user_id or not isinstance(user_id, str):
            raise ValueError("User ID must be a non-empty string")
        
        if not example:
            raise ValueError("Example must be provided")
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Determine difficulty level from example
        try:
            from .models import DifficultyLevel
            level = DifficultyLevel(example.difficulty)
        except (ValueError, AttributeError):
            level = DifficultyLevel.BEGINNER
        
        # Create exercises based on the example
        exercises = []
        
        # Create main exercise from the example
        main_exercise = InteractiveExercise(
            id=str(uuid.uuid4()),
            title=f"Practice: {example.title}",
            description=f"{example.description}\n\nExample code:\n{example.code}",
            starter_code=f"# Based on the example above, try to write similar code\n# {example.explanation}\n\n",
            expected_output=getattr(example, 'expected_output', 'Working code implementation'),
            hints=[
                "Look at the example code for guidance",
                "Break the problem into smaller steps",
                "Test your code as you write it"
            ] + getattr(example, 'common_mistakes', []),
            difficulty_level=level,
            topic=example.topics[0] if example.topics else "general",
            status=ExerciseStatus.NOT_STARTED
        )
        exercises.append(main_exercise)
        
        # Create the session
        session = TutorialSession(
            session_id=session_id,
            topic=example.topics[0] if example.topics else "general",
            level=level,
            start_time=datetime.now(),
            exercises=exercises,
            current_exercise_index=0,
            is_completed=False
        )
        
        # Store the session
        self._active_sessions[session_id] = session
        
        return session
    
    def get_session(self, session_id: str) -> Optional[TutorialSession]:
        """
        Get an active session by ID.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Optional[TutorialSession]: Session or None if not found
        """
        if not session_id or not isinstance(session_id, str):
            return None
        
        return self._active_sessions.get(session_id)
    
    def submit_solution(self, session_id: str, solution: str) -> ValidationResult:
        """
        Submit a solution for the current exercise in the session.
        
        Args:
            session_id: Unique session identifier
            solution: User's code solution
            
        Returns:
            ValidationResult: Validation result with feedback
        """
        session = self.get_session(session_id)
        if not session:
            return ValidationResult(
                is_correct=False,
                feedback="Session not found",
                errors=["Invalid session ID"]
            )
        
        if session.is_completed:
            return ValidationResult(
                is_correct=False,
                feedback="Session is already completed",
                errors=["Session completed"]
            )
        
        # Get current exercise
        current_exercise = self._get_current_exercise(session)
        if not current_exercise:
            return ValidationResult(
                is_correct=False,
                feedback="No active exercise in session",
                errors=["No exercise available"]
            )
        
        # Update exercise status and attempt count
        current_exercise.status = ExerciseStatus.IN_PROGRESS
        current_exercise.attempts += 1
        
        # Validate the solution using the tutorial engine
        result = self._tutorial_engine.validate_solution(current_exercise, solution)
        
        # Update exercise status based on result
        if result.is_correct:
            current_exercise.status = ExerciseStatus.COMPLETED
            # Add encouraging feedback for correct solutions
            result.feedback = f"Excellent work! {result.feedback}"
            result.suggestions.append("Ready for the next challenge!")
        else:
            # Check if max attempts reached
            if current_exercise.attempts >= current_exercise.max_attempts:
                current_exercise.status = ExerciseStatus.FAILED
                result.feedback += " You've reached the maximum attempts. Let's move to the next exercise."
                result.suggestions.append("Don't worry, learning takes practice!")
        
        return result
    
    def get_hint(self, session_id: str) -> Optional[str]:
        """
        Get a hint for the current exercise in the session.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Optional[str]: Hint text or None if no hints available
        """
        session = self.get_session(session_id)
        if not session:
            return None
        
        current_exercise = self._get_current_exercise(session)
        if not current_exercise:
            return None
        
        # Get hint from tutorial engine based on current attempt
        hint = self._tutorial_engine.provide_hint(current_exercise, "")
        
        return hint
    
    def next_exercise(self, session_id: str) -> Optional[InteractiveExercise]:
        """
        Move to the next exercise in the session.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Optional[InteractiveExercise]: Next exercise or None if session complete
        """
        session = self.get_session(session_id)
        if not session:
            return None
        
        # Move to next exercise
        session.current_exercise_index += 1
        
        # Check if session is complete
        if session.current_exercise_index >= len(session.exercises):
            session.is_completed = True
            session.end_time = datetime.now()
            return None
        
        # Return the next exercise
        return session.exercises[session.current_exercise_index]
    
    def complete_session(self, session_id: str) -> Dict[str, Any]:
        """
        Complete the session and return summary statistics.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Dict[str, Any]: Session completion summary
        """
        session = self.get_session(session_id)
        if not session:
            return {"error": "Session not found"}
        
        # Mark session as completed if not already
        if not session.is_completed:
            session.is_completed = True
            session.end_time = datetime.now()
        
        # Calculate statistics
        total_exercises = len(session.exercises)
        completed_exercises = sum(1 for ex in session.exercises if ex.status == ExerciseStatus.COMPLETED)
        failed_exercises = sum(1 for ex in session.exercises if ex.status == ExerciseStatus.FAILED)
        total_attempts = sum(ex.attempts for ex in session.exercises)
        
        # Calculate session duration
        duration_minutes = 0
        if session.end_time and session.start_time:
            duration = session.end_time - session.start_time
            duration_minutes = duration.total_seconds() / 60
        
        # Calculate success rate
        success_rate = (completed_exercises / total_exercises * 100) if total_exercises > 0 else 0
        
        # Generate feedback message
        if success_rate >= 80:
            feedback = "Outstanding performance! You're mastering this topic."
        elif success_rate >= 60:
            feedback = "Good job! Keep practicing to improve further."
        elif success_rate >= 40:
            feedback = "You're making progress. Don't give up!"
        else:
            feedback = "Learning takes time. Consider reviewing the basics and trying again."
        
        # Remove session from active sessions
        if session_id in self._active_sessions:
            del self._active_sessions[session_id]
        
        return {
            "session_id": session_id,
            "topic": session.topic,
            "level": session.level.value,
            "duration_minutes": round(duration_minutes, 2),
            "total_exercises": total_exercises,
            "completed_exercises": completed_exercises,
            "failed_exercises": failed_exercises,
            "total_attempts": total_attempts,
            "success_rate": round(success_rate, 2),
            "feedback": feedback,
            "completed_at": session.end_time.isoformat() if session.end_time else None
        }
    
    def provide_additional_examples(self, session_id: str, topic: str) -> List[str]:
        """
        Provide additional examples when user is struggling.
        
        Args:
            session_id: Unique session identifier
            topic: Topic for which to provide examples
            
        Returns:
            List[str]: List of additional example descriptions
        """
        session = self.get_session(session_id)
        if not session:
            return []
        
        topic_lower = topic.lower()
        
        # Get examples for the topic
        examples = self._additional_examples.get(topic_lower, [])
        
        # If no specific examples, provide generic encouragement
        if not examples:
            examples = [
                f"Try breaking down the {topic} problem into smaller steps",
                f"Look for similar {topic} examples online or in documentation",
                f"Practice with simpler {topic} exercises first",
                "Don't hesitate to ask for help when you're stuck"
            ]
        
        return examples
    
    def get_current_exercise(self, session_id: str) -> Optional[InteractiveExercise]:
        """
        Get the current exercise for a session.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Optional[InteractiveExercise]: Current exercise or None
        """
        session = self.get_session(session_id)
        if not session:
            return None
        
        return self._get_current_exercise(session)
    
    def get_session_progress(self, session_id: str) -> Dict[str, Any]:
        """
        Get progress information for a session.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Dict[str, Any]: Progress information
        """
        session = self.get_session(session_id)
        if not session:
            return {"error": "Session not found"}
        
        total_exercises = len(session.exercises)
        current_index = session.current_exercise_index
        completed_exercises = sum(1 for ex in session.exercises if ex.status == ExerciseStatus.COMPLETED)
        
        progress_percentage = (completed_exercises / total_exercises * 100) if total_exercises > 0 else 0
        
        return {
            "session_id": session_id,
            "topic": session.topic,
            "level": session.level.value,
            "current_exercise": current_index + 1,
            "total_exercises": total_exercises,
            "completed_exercises": completed_exercises,
            "progress_percentage": round(progress_percentage, 2),
            "is_completed": session.is_completed
        }
    
    def _get_current_exercise(self, session: TutorialSession) -> Optional[InteractiveExercise]:
        """Get the current exercise from a session."""
        if (session.current_exercise_index < 0 or 
            session.current_exercise_index >= len(session.exercises)):
            return None
        
        return session.exercises[session.current_exercise_index]
    
    def _create_follow_up_exercise(self, topic: str, level: DifficultyLevel) -> Optional[InteractiveExercise]:
        """Create a follow-up exercise for the topic."""
        topic_lower = topic.lower()
        
        # Define follow-up exercises for different topics
        follow_up_templates = {
            'variables': {
                'title': 'Variable Operations',
                'description': 'Practice using variables in calculations and operations.',
                'starter_code': '# Use the variables you created to perform some operations\n# For example, if you have age and name, create a message\n',
                'hints': [
                    'You can combine variables with strings using f-strings',
                    'Try doing math operations with number variables',
                    'Use descriptive variable names'
                ]
            },
            'lists': {
                'title': 'List Manipulation',
                'description': 'Practice adding, removing, and accessing list elements.',
                'starter_code': '# Take your list and try adding a new item\n# Then remove an item and print the result\n',
                'hints': [
                    'Use append() to add items',
                    'Use remove() to delete items by value',
                    'Use len() to get the list size'
                ]
            },
            'functions': {
                'title': 'Function with Return Value',
                'description': 'Create a function that takes parameters and returns a result.',
                'starter_code': '# Create a function that takes two numbers and returns their sum\n# Then call it and print the result\n',
                'hints': [
                    'Use parameters inside the parentheses',
                    'Use return to send a value back',
                    'Store the returned value in a variable'
                ]
            }
        }
        
        template = follow_up_templates.get(topic_lower)
        if not template:
            return None
        
        return InteractiveExercise(
            id=str(uuid.uuid4()),
            title=template['title'],
            description=template['description'],
            starter_code=template['starter_code'],
            expected_output="Follow-up exercise completion",
            hints=template['hints'],
            difficulty_level=level,
            topic=topic,
            status=ExerciseStatus.NOT_STARTED
        )