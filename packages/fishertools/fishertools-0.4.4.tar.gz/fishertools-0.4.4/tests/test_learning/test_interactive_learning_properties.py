"""
Property-based tests for Interactive Learning completeness.

Feature: fishertools-enhancements
Property 5: Interactive Learning Completeness
Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5
"""

import pytest
from hypothesis import given, strategies as st, assume
from fishertools.learning.session import InteractiveSessionManager
from fishertools.learning.tutorial import TutorialEngine
from fishertools.learning.models import DifficultyLevel, ExerciseStatus


class TestInteractiveLearningCompleteness:
    """Property tests for Interactive Learning completeness."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.session_manager = InteractiveSessionManager()
        self.tutorial_engine = TutorialEngine()
    
    @given(
        user_id=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
        topic=st.sampled_from(["variables", "lists", "functions", "loops", "conditionals"]),
        level=st.sampled_from([DifficultyLevel.BEGINNER, DifficultyLevel.INTERMEDIATE, DifficultyLevel.ADVANCED])
    )
    def test_interactive_session_creation_completeness(self, user_id, topic, level):
        """
        Property 5: For any learning session, the Learning_System should 
        provide interactive exercises with proper session management.
        
        **Validates: Requirements 5.1**
        """
        assume(len(user_id.strip()) > 0)
        
        user_id = user_id.strip()
        
        # Test session creation
        session = self.session_manager.create_session(user_id, topic, level)
        
        # Property: Session should be created successfully
        assert session is not None, "Interactive session should be created"
        assert session.session_id, "Session should have a unique ID"
        assert session.topic == topic, "Session topic should match requested topic"
        assert session.level == level, "Session level should match requested level"
        assert isinstance(session.exercises, list), "Session should have exercises list"
        assert len(session.exercises) > 0, "Session should have at least one exercise"
        assert session.current_exercise_index == 0, "Should start with first exercise"
        assert not session.is_completed, "New session should not be completed"
        
        # Property: Session should be retrievable
        retrieved_session = self.session_manager.get_session(session.session_id)
        assert retrieved_session is not None, "Session should be retrievable"
        assert retrieved_session.session_id == session.session_id, "Retrieved session should match"
        
        # Property: Each exercise should be properly formed
        for exercise in session.exercises:
            assert exercise.id, "Exercise should have an ID"
            assert exercise.title, "Exercise should have a title"
            assert exercise.description, "Exercise should have a description"
            assert exercise.starter_code is not None, "Exercise should have starter code"
            assert isinstance(exercise.hints, list), "Exercise should have hints list"
            assert exercise.difficulty_level == level, "Exercise difficulty should match session level"
            assert exercise.topic == topic, "Exercise topic should match session topic"
            assert exercise.status == ExerciseStatus.NOT_STARTED, "New exercises should not be started"
    
    @given(
        topic=st.sampled_from(["variables", "lists", "functions", "loops"]),
        level=st.sampled_from([DifficultyLevel.BEGINNER, DifficultyLevel.INTERMEDIATE])
    )
    def test_exercise_creation_completeness(self, topic, level):
        """
        Property 5: For any learning session, the Learning_System should 
        create appropriate interactive exercises for the topic and level.
        
        **Validates: Requirements 5.1, 5.2**
        """
        # Test exercise creation
        exercise = self.tutorial_engine.create_interactive_exercise(topic, level)
        
        # Property: Exercise should be created with all required components
        assert exercise is not None, "Exercise should be created"
        assert exercise.id, "Exercise should have a unique ID"
        assert exercise.title, "Exercise should have a title"
        assert exercise.description, "Exercise should have a description"
        assert exercise.starter_code is not None, "Exercise should have starter code"
        assert exercise.expected_output, "Exercise should have expected output"
        assert isinstance(exercise.hints, list), "Exercise should have hints list"
        assert len(exercise.hints) > 0, "Exercise should have at least one hint"
        assert exercise.difficulty_level == level, "Exercise difficulty should match requested level"
        assert exercise.topic == topic, "Exercise topic should match requested topic"
        assert exercise.status == ExerciseStatus.NOT_STARTED, "New exercise should not be started"
        assert exercise.attempts == 0, "New exercise should have 0 attempts"
        assert exercise.max_attempts > 0, "Exercise should have maximum attempts limit"
    
    @given(
        topic=st.sampled_from(["variables", "lists", "functions"]),
        solution=st.text(min_size=1, max_size=200)
    )
    def test_solution_validation_completeness(self, topic, solution):
        """
        Property 5: For any learning session, the Learning_System should 
        validate solutions and provide appropriate feedback.
        
        **Validates: Requirements 5.2, 5.3**
        """
        assume(len(solution.strip()) > 0)
        
        # Create exercise for testing
        exercise = self.tutorial_engine.create_interactive_exercise(topic, DifficultyLevel.BEGINNER)
        
        # Test solution validation
        result = self.tutorial_engine.validate_solution(exercise, solution)
        
        # Property: Validation should always return a result
        assert result is not None, "Validation should return a result"
        assert hasattr(result, 'is_correct'), "Result should have is_correct attribute"
        assert hasattr(result, 'feedback'), "Result should have feedback attribute"
        assert hasattr(result, 'errors'), "Result should have errors attribute"
        assert hasattr(result, 'suggestions'), "Result should have suggestions attribute"
        
        # Property: Feedback should be provided
        assert isinstance(result.feedback, str), "Feedback should be a string"
        assert len(result.feedback) > 0, "Feedback should not be empty"
        
        # Property: Errors and suggestions should be lists
        assert isinstance(result.errors, list), "Errors should be a list"
        assert isinstance(result.suggestions, list), "Suggestions should be a list"
        
        # Property: If incorrect, should provide helpful information
        if not result.is_correct:
            assert len(result.errors) > 0 or len(result.suggestions) > 0, "Should provide errors or suggestions for incorrect solutions"
    
    @given(
        topic=st.sampled_from(["variables", "lists", "functions"]),
        attempt=st.text(max_size=100)
    )
    def test_hint_provision_completeness(self, topic, attempt):
        """
        Property 5: For any learning session, the Learning_System should 
        provide hints when users need help.
        
        **Validates: Requirements 5.3**
        """
        # Create exercise for testing
        exercise = self.tutorial_engine.create_interactive_exercise(topic, DifficultyLevel.BEGINNER)
        
        # Test hint provision
        hint = self.tutorial_engine.provide_hint(exercise, attempt)
        
        # Property: Should always provide a hint
        assert hint is not None, "Should provide a hint"
        assert isinstance(hint, str), "Hint should be a string"
        assert len(hint) > 0, "Hint should not be empty"
        
        # Property: Hint should be helpful and relevant
        assert len(hint) > 10, "Hint should be substantial enough to be helpful"
        
        # Property: Multiple hint requests should work
        hint2 = self.tutorial_engine.provide_hint(exercise, attempt + " more code")
        assert hint2 is not None, "Should provide multiple hints"
        assert isinstance(hint2, str), "Second hint should be a string"
    
    @given(
        topic=st.sampled_from(["variables", "lists", "functions"])
    )
    def test_solution_explanation_completeness(self, topic):
        """
        Property 5: For any learning session, the Learning_System should 
        provide detailed explanations of exercise solutions.
        
        **Validates: Requirements 5.4**
        """
        # Create exercise for testing
        exercise = self.tutorial_engine.create_interactive_exercise(topic, DifficultyLevel.BEGINNER)
        
        # Test solution explanation
        explanations = self.tutorial_engine.explain_solution(exercise)
        
        # Property: Should provide explanations
        assert explanations is not None, "Should provide solution explanations"
        assert isinstance(explanations, list), "Explanations should be a list"
        
        # Property: Each explanation should be well-formed
        for explanation in explanations:
            assert hasattr(explanation, 'step_number'), "Explanation should have step number"
            assert hasattr(explanation, 'description'), "Explanation should have description"
            assert hasattr(explanation, 'code_snippet'), "Explanation should have code snippet"
            assert hasattr(explanation, 'related_concepts'), "Explanation should have related concepts"
            
            assert explanation.step_number > 0, "Step number should be positive"
            assert isinstance(explanation.description, str), "Description should be a string"
            assert len(explanation.description) > 0, "Description should not be empty"
            assert isinstance(explanation.code_snippet, str), "Code snippet should be a string"
            assert isinstance(explanation.related_concepts, list), "Related concepts should be a list"
    
    @given(
        user_id=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
        topic=st.sampled_from(["variables", "lists", "functions"])
    )
    def test_additional_examples_provision_completeness(self, user_id, topic):
        """
        Property 5: For any learning session, the Learning_System should 
        provide additional examples when users struggle.
        
        **Validates: Requirements 5.5**
        """
        assume(len(user_id.strip()) > 0)
        
        user_id = user_id.strip()
        
        # Create session
        session = self.session_manager.create_session(user_id, topic, DifficultyLevel.BEGINNER)
        
        # Test additional examples provision
        examples = self.session_manager.provide_additional_examples(session.session_id, topic)
        
        # Property: Should provide additional examples
        assert examples is not None, "Should provide additional examples"
        assert isinstance(examples, list), "Examples should be a list"
        assert len(examples) > 0, "Should provide at least one example"
        
        # Property: Each example should be helpful
        for example in examples:
            assert isinstance(example, str), "Each example should be a string"
            assert len(example) > 0, "Examples should not be empty"
            assert len(example) > 10, "Examples should be substantial enough to be helpful"
    
    @given(
        user_id=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
        topic=st.sampled_from(["variables", "lists", "functions"])
    )
    def test_session_workflow_completeness(self, user_id, topic):
        """
        Property 5: For any learning session, the complete workflow should 
        work from creation to completion.
        
        **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**
        """
        assume(len(user_id.strip()) > 0)
        
        user_id = user_id.strip()
        
        # Create session
        session = self.session_manager.create_session(user_id, topic, DifficultyLevel.BEGINNER)
        
        # Property: Should be able to get current exercise
        current_exercise = self.session_manager.get_current_exercise(session.session_id)
        assert current_exercise is not None, "Should have a current exercise"
        
        # Property: Should be able to get session progress
        progress = self.session_manager.get_session_progress(session.session_id)
        assert progress is not None, "Should provide session progress"
        assert 'session_id' in progress, "Progress should include session ID"
        assert 'topic' in progress, "Progress should include topic"
        assert 'current_exercise' in progress, "Progress should include current exercise"
        assert 'total_exercises' in progress, "Progress should include total exercises"
        assert 'progress_percentage' in progress, "Progress should include progress percentage"
        
        # Property: Should be able to get hints
        hint = self.session_manager.get_hint(session.session_id)
        assert hint is not None, "Should provide hints"
        assert isinstance(hint, str), "Hint should be a string"
        
        # Property: Should be able to submit solutions (even if incorrect)
        test_solution = "# test solution"
        result = self.session_manager.submit_solution(session.session_id, test_solution)
        assert result is not None, "Should validate solutions"
        
        # Property: Should be able to complete session
        summary = self.session_manager.complete_session(session.session_id)
        assert summary is not None, "Should provide completion summary"
        assert 'session_id' in summary, "Summary should include session ID"
        assert 'topic' in summary, "Summary should include topic"
        assert 'success_rate' in summary, "Summary should include success rate"
        assert 'feedback' in summary, "Summary should include feedback"
    
    def test_error_handling_completeness(self):
        """
        Property 5: Interactive learning system should handle errors gracefully.
        
        **Validates: Requirements 5.1, 5.2, 5.3**
        """
        # Property: Invalid session IDs should be handled gracefully
        assert self.session_manager.get_session("invalid_id") is None, "Invalid session ID should return None"
        assert self.session_manager.get_hint("invalid_id") is None, "Invalid session ID should return None for hints"
        
        # Property: Invalid user inputs should be handled gracefully
        with pytest.raises(ValueError):
            self.session_manager.create_session("", "topic", DifficultyLevel.BEGINNER)
        
        with pytest.raises(ValueError):
            self.session_manager.create_session("user", "", DifficultyLevel.BEGINNER)
        
        # Property: Empty solutions should be handled gracefully
        exercise = self.tutorial_engine.create_interactive_exercise("variables", DifficultyLevel.BEGINNER)
        result = self.tutorial_engine.validate_solution(exercise, "")
        assert result is not None, "Should handle empty solutions"
        assert not result.is_correct, "Empty solution should be incorrect"
        assert len(result.feedback) > 0, "Should provide feedback for empty solutions"
        
        # Property: Invalid code should be handled gracefully
        invalid_code_result = self.tutorial_engine.validate_solution(exercise, "invalid python code !!!")
        assert invalid_code_result is not None, "Should handle invalid code"
        assert not invalid_code_result.is_correct, "Invalid code should be incorrect"
    
    @given(
        topic=st.sampled_from(["variables", "lists", "functions"]),
        code_line=st.text(min_size=1, max_size=100).filter(lambda x: x.strip())
    )
    def test_step_explanation_integration_completeness(self, topic, code_line):
        """
        Property 5: Interactive learning should integrate with step-by-step explanations.
        
        **Validates: Requirements 5.4**
        """
        assume(len(code_line.strip()) > 0)
        
        # Test step explanation generation
        try:
            explanation = self.tutorial_engine.generate_step_explanation(code_line.strip())
            
            # Property: Should generate explanations for valid code
            assert explanation is not None, "Should generate explanation"
            assert hasattr(explanation, 'description'), "Should have description"
            assert hasattr(explanation, 'code_snippet'), "Should have code snippet"
            assert hasattr(explanation, 'related_concepts'), "Should have related concepts"
            
            # Property: Explanation should be informative
            assert len(explanation.description) > 0, "Description should not be empty"
            assert explanation.code_snippet == code_line.strip(), "Code snippet should match input"
            
        except ValueError:
            # Invalid code should raise ValueError, which is acceptable
            pass