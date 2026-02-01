"""
Property-based tests for SessionManager using Hypothesis.

**Validates: Requirements 6.5, 6.6, 9.4, 9.5**
"""

import pytest
import tempfile
from hypothesis import given, strategies as st, assume
from fishertools.learn.repl.session_manager import SessionManager


class TestSessionManagerProperties:
    """Property-based tests for session management."""
    
    @given(st.text(min_size=1, max_size=100))
    def test_mark_topic_viewed_consistency(self, topic_name):
        """
        For any topic name, marking it as viewed should make it appear in viewed topics.
        
        **Validates: Requirements 6.5, 6.6, 9.4, 9.5**
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(tmpdir)
            manager.mark_topic_viewed(topic_name)
            
            viewed = manager.get_viewed_topics()
            assert topic_name in viewed
    
    @given(st.text(min_size=1, max_size=100), st.integers(min_value=1, max_value=100))
    def test_mark_example_executed_consistency(self, topic_name, example_num):
        """
        For any topic and example number, marking it as executed should make it appear in executed examples.
        
        **Validates: Requirements 6.5, 6.6, 9.4, 9.5**
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(tmpdir)
            manager.mark_example_executed(topic_name, example_num)
            
            executed = manager.get_executed_examples()
            assert topic_name in executed
            assert example_num in executed[topic_name]
    
    @given(st.text(min_size=1, max_size=100))
    def test_session_persistence_round_trip(self, topic_name):
        """
        Property 7: Session State Persistence Round-Trip
        
        For any session state saved to disk, loading it should restore the exact same state.
        
        **Validates: Requirements 6.5, 6.6, 9.4, 9.5**
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create and save session
            manager1 = SessionManager(tmpdir)
            manager1.mark_topic_viewed(topic_name)
            manager1.set_current_topic(topic_name)
            manager1.save_session()
            
            # Load session
            manager2 = SessionManager(tmpdir)
            
            # Verify state is identical
            assert manager2.get_current_topic() == topic_name
            assert topic_name in manager2.get_viewed_topics()
    
    @given(st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=10, unique=True))
    def test_multiple_topics_persistence(self, topic_names):
        """
        For any list of topics, saving and loading should preserve all topics.
        
        **Validates: Requirements 6.5, 6.6, 9.4, 9.5**
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create and save session with multiple topics
            manager1 = SessionManager(tmpdir)
            for topic in topic_names:
                manager1.mark_topic_viewed(topic)
            manager1.save_session()
            
            # Load and verify
            manager2 = SessionManager(tmpdir)
            viewed = manager2.get_viewed_topics()
            
            for topic in topic_names:
                assert topic in viewed
    
    @given(st.text(min_size=1, max_size=100), st.lists(st.integers(min_value=1, max_value=50), min_size=1, max_size=10, unique=True))
    def test_executed_examples_persistence(self, topic_name, example_nums):
        """
        For any topic and list of example numbers, saving and loading should preserve all executed examples.
        
        **Validates: Requirements 6.5, 6.6, 9.4, 9.5**
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create and save session with executed examples
            manager1 = SessionManager(tmpdir)
            for example_num in example_nums:
                manager1.mark_example_executed(topic_name, example_num)
            manager1.save_session()
            
            # Load and verify
            manager2 = SessionManager(tmpdir)
            executed = manager2.get_executed_examples()
            
            assert topic_name in executed
            for example_num in example_nums:
                assert example_num in executed[topic_name]
    
    @given(st.text(min_size=1, max_size=100))
    def test_current_topic_persistence(self, topic_name):
        """
        For any current topic, saving and loading should preserve it.
        
        **Validates: Requirements 6.5, 6.6, 9.4, 9.5**
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create and save session
            manager1 = SessionManager(tmpdir)
            manager1.set_current_topic(topic_name)
            manager1.save_session()
            
            # Load and verify
            manager2 = SessionManager(tmpdir)
            assert manager2.get_current_topic() == topic_name
    
    @given(st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=10, unique=True))
    def test_session_history_persistence(self, topic_names):
        """
        For any sequence of topics, saving and loading should preserve the session history.
        
        **Validates: Requirements 6.5, 6.6, 9.4, 9.5**
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create and save session with history
            manager1 = SessionManager(tmpdir)
            for topic in topic_names:
                manager1.mark_topic_viewed(topic)
            manager1.save_session()
            
            # Load and verify
            manager2 = SessionManager(tmpdir)
            history = manager2.get_session_history()
            
            assert len(history) == len(topic_names)
            for i, topic in enumerate(topic_names):
                assert history[i] == topic
    
    @given(st.text(min_size=1, max_size=100))
    def test_is_topic_viewed_after_persistence(self, topic_name):
        """
        For any topic marked as viewed, after persistence it should still be marked as viewed.
        
        **Validates: Requirements 6.5, 6.6, 9.4, 9.5**
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create and save session
            manager1 = SessionManager(tmpdir)
            manager1.mark_topic_viewed(topic_name)
            manager1.save_session()
            
            # Load and verify
            manager2 = SessionManager(tmpdir)
            assert manager2.is_topic_viewed(topic_name) is True
    
    @given(st.text(min_size=1, max_size=100), st.integers(min_value=1, max_value=50))
    def test_is_example_executed_after_persistence(self, topic_name, example_num):
        """
        For any example marked as executed, after persistence it should still be marked as executed.
        
        **Validates: Requirements 6.5, 6.6, 9.4, 9.5**
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create and save session
            manager1 = SessionManager(tmpdir)
            manager1.mark_example_executed(topic_name, example_num)
            manager1.save_session()
            
            # Load and verify
            manager2 = SessionManager(tmpdir)
            assert manager2.is_example_executed(topic_name, example_num) is True
