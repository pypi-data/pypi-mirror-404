"""
Property-based tests for Learning System completeness.

Feature: fishertools-enhancements
Property 1: Learning System Completeness
Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5
"""

import pytest
from hypothesis import given, strategies as st, assume
from fishertools.learning import LearningSystem
from fishertools.learning.models import DifficultyLevel, CodeContext


class TestLearningSystemCompleteness:
    """Property tests for Learning System completeness."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.learning_system = LearningSystem()
    
    @given(
        topic=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
        level=st.sampled_from(["beginner", "intermediate", "advanced"])
    )
    def test_step_by_step_explanation_completeness(self, topic, level):
        """
        Property 1: For any fishertools function used by a beginner, 
        the Learning_System should provide step-by-step explanations 
        that include input/output examples, related topics, and 
        level-appropriate content adaptation.
        
        **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5**
        """
        # Generate simple Python code for testing
        test_codes = [
            "x = 5",
            "my_list = [1, 2, 3]",
            "def greet(name): return f'Hello {name}'",
            "if x > 0: print('positive')",
            "for i in range(3): print(i)"
        ]
        
        for code in test_codes:
            # Test that explanations are provided
            explanations = self.learning_system.get_step_by_step_explanation(code)
            
            # Property: Should always provide explanations for valid code
            assert len(explanations) > 0, f"No explanations provided for code: {code}"
            
            # Property: Each explanation should have required components
            for explanation in explanations:
                assert explanation.step_number > 0, "Step number should be positive"
                assert explanation.description, "Description should not be empty"
                assert explanation.code_snippet, "Code snippet should not be empty"
                assert isinstance(explanation.related_concepts, list), "Related concepts should be a list"
    
    @given(
        topic=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
        level=st.sampled_from(["beginner", "intermediate", "advanced"])
    )
    def test_tutorial_session_creation_completeness(self, topic, level):
        """
        Property 1: For any topic request, the Learning_System should 
        create a tutorial session with appropriate exercises and content.
        
        **Validates: Requirements 1.1, 1.4, 1.5**
        """
        assume(len(topic.strip()) > 0)
        
        try:
            # Test tutorial session creation
            session = self.learning_system.start_tutorial(topic, level)
            
            # Property: Session should be created successfully
            assert session is not None, "Tutorial session should be created"
            assert session.topic == topic, "Session topic should match requested topic"
            assert session.level.value == level, "Session level should match requested level"
            assert session.session_id, "Session should have a unique ID"
            assert isinstance(session.exercises, list), "Session should have exercises list"
            
        except ValueError as e:
            # Invalid inputs should raise ValueError, which is acceptable
            assert "Invalid" in str(e) or "must be" in str(e)
    
    @given(
        current_topic=st.text(min_size=1, max_size=50).filter(lambda x: x.strip())
    )
    def test_related_topics_suggestion_completeness(self, current_topic):
        """
        Property 1: For any current topic, the Learning_System should 
        suggest related topics for further learning.
        
        **Validates: Requirements 1.4, 1.5**
        """
        assume(len(current_topic.strip()) > 0)
        
        # Test related topics suggestion
        related_topics = self.learning_system.suggest_related_topics(current_topic)
        
        # Property: Should return a list (may be empty for unknown topics)
        assert isinstance(related_topics, list), "Related topics should be a list"
        
        # Property: All suggested topics should be strings
        for topic in related_topics:
            assert isinstance(topic, str), "Each related topic should be a string"
            assert len(topic.strip()) > 0, "Related topics should not be empty strings"
        
        # Property: Should not suggest more than reasonable number of topics
        assert len(related_topics) <= 10, "Should not suggest too many topics"
    
    @given(
        content=st.text(min_size=1, max_size=200),
        level=st.sampled_from(["beginner", "intermediate", "advanced"])
    )
    def test_content_adaptation_completeness(self, content, level):
        """
        Property 1: For any content and level, the Learning_System should 
        adapt content appropriately for the specified difficulty level.
        
        **Validates: Requirements 1.5**
        """
        assume(len(content.strip()) > 0)
        
        # Test content adaptation
        adapted_content = self.learning_system.adapt_content_for_level(content, level)
        
        # Property: Should return adapted content
        assert isinstance(adapted_content, str), "Adapted content should be a string"
        assert len(adapted_content) > 0, "Adapted content should not be empty"
        
        # Property: Beginner content should be more detailed
        if level == "beginner":
            # Beginner content often has additional explanatory text
            assert len(adapted_content) >= len(content) * 0.8, "Beginner content should maintain or increase length"
    
    @given(
        code=st.text(min_size=1, max_size=100).filter(lambda x: x.strip())
    )
    def test_explanation_with_context_completeness(self, code):
        """
        Property 1: For any code with context, the Learning_System should 
        provide enhanced explanations using the context information.
        
        **Validates: Requirements 1.2, 1.3**
        """
        assume(len(code.strip()) > 0)
        
        # Create context
        context = CodeContext(
            function_name="test_function",
            variables={"x": 5, "name": "test"}
        )
        
        try:
            # Test explanation with context
            explanations = self.learning_system.get_step_by_step_explanation(code, context)
            
            # Property: Should provide explanations even with context
            assert isinstance(explanations, list), "Explanations should be a list"
            
            # Property: Each explanation should be well-formed
            for explanation in explanations:
                assert hasattr(explanation, 'step_number'), "Should have step number"
                assert hasattr(explanation, 'description'), "Should have description"
                assert hasattr(explanation, 'code_snippet'), "Should have code snippet"
                
        except (SyntaxError, ValueError):
            # Invalid code should be handled gracefully
            pass
    
    def test_learning_system_initialization_completeness(self):
        """
        Property 1: Learning System should initialize properly and 
        provide all required functionality.
        
        **Validates: Requirements 1.1**
        """
        # Test initialization
        system = LearningSystem()
        
        # Property: Should have all required methods
        required_methods = [
            'start_tutorial',
            'get_step_by_step_explanation', 
            'suggest_related_topics',
            'adapt_content_for_level',
            'track_progress',
            'get_user_progress'
        ]
        
        for method_name in required_methods:
            assert hasattr(system, method_name), f"Should have {method_name} method"
            assert callable(getattr(system, method_name)), f"{method_name} should be callable"