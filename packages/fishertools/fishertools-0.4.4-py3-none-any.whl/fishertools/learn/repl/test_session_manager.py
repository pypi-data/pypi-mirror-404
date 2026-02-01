"""
Unit tests for the SessionManager class.
"""

import pytest
import json
import tempfile
from pathlib import Path
from fishertools.learn.repl.session_manager import SessionManager


class TestSessionManagerBasic:
    """Test basic session manager functionality."""
    
    def test_create_session_manager(self):
        """Test creating a session manager."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(tmpdir)
            assert manager.storage_path == Path(tmpdir)
            assert manager.storage_path == Path(tmpdir)
    
    def test_mark_topic_viewed(self):
        """Test marking a topic as viewed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(tmpdir)
            manager.mark_topic_viewed("Lists")
            
            viewed = manager.get_viewed_topics()
            assert "Lists" in viewed
    
    def test_mark_multiple_topics_viewed(self):
        """Test marking multiple topics as viewed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(tmpdir)
            manager.mark_topic_viewed("Lists")
            manager.mark_topic_viewed("Dictionaries")
            manager.mark_topic_viewed("For Loops")
            
            viewed = manager.get_viewed_topics()
            assert len(viewed) == 3
            assert "Lists" in viewed
            assert "Dictionaries" in viewed
            assert "For Loops" in viewed
    
    def test_mark_example_executed(self):
        """Test marking an example as executed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(tmpdir)
            manager.mark_example_executed("Lists", 1)
            
            executed = manager.get_executed_examples()
            assert "Lists" in executed
            assert 1 in executed["Lists"]
    
    def test_mark_multiple_examples_executed(self):
        """Test marking multiple examples as executed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(tmpdir)
            manager.mark_example_executed("Lists", 1)
            manager.mark_example_executed("Lists", 2)
            manager.mark_example_executed("Dictionaries", 1)
            
            executed = manager.get_executed_examples()
            assert len(executed["Lists"]) == 2
            assert len(executed["Dictionaries"]) == 1


class TestSessionManagerProgress:
    """Test progress tracking functionality."""
    
    def test_get_progress_empty(self):
        """Test getting progress with no activity."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(tmpdir)
            progress = manager.get_progress()
            
            assert progress.viewed_topics == 0
            assert progress.executed_examples == 0
    
    def test_get_progress_with_activity(self):
        """Test getting progress with activity."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(tmpdir)
            manager.mark_topic_viewed("Lists")
            manager.mark_topic_viewed("Dictionaries")
            manager.mark_example_executed("Lists", 1)
            manager.mark_example_executed("Lists", 2)
            
            progress = manager.get_progress()
            assert progress.viewed_topics == 2
            assert progress.executed_examples == 2
    
    def test_progress_stats_structure(self):
        """Test that progress stats have correct structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(tmpdir)
            progress = manager.get_progress()
            
            assert hasattr(progress, 'total_topics')
            assert hasattr(progress, 'viewed_topics')
            assert hasattr(progress, 'total_examples')
            assert hasattr(progress, 'executed_examples')
            assert hasattr(progress, 'session_duration')


class TestSessionManagerCurrentTopic:
    """Test current topic tracking."""
    
    def test_set_current_topic(self):
        """Test setting current topic."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(tmpdir)
            manager.set_current_topic("Lists")
            
            current = manager.get_current_topic()
            assert current == "Lists"
    
    def test_current_topic_none_initially(self):
        """Test that current topic is None initially."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(tmpdir)
            current = manager.get_current_topic()
            assert current is None
    
    def test_change_current_topic(self):
        """Test changing current topic."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(tmpdir)
            manager.set_current_topic("Lists")
            manager.set_current_topic("Dictionaries")
            
            current = manager.get_current_topic()
            assert current == "Dictionaries"


class TestSessionManagerHistory:
    """Test session history tracking."""
    
    def test_session_history_empty_initially(self):
        """Test that session history is empty initially."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(tmpdir)
            history = manager.get_session_history()
            assert len(history) == 0
    
    def test_session_history_tracks_topics(self):
        """Test that session history tracks viewed topics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(tmpdir)
            manager.mark_topic_viewed("Lists")
            manager.mark_topic_viewed("Dictionaries")
            manager.mark_topic_viewed("For Loops")
            
            history = manager.get_session_history()
            assert len(history) == 3
            assert history[0] == "Lists"
            assert history[1] == "Dictionaries"
            assert history[2] == "For Loops"
    
    def test_session_history_no_duplicates(self):
        """Test that session history doesn't add duplicate consecutive topics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(tmpdir)
            manager.mark_topic_viewed("Lists")
            manager.mark_topic_viewed("Lists")
            manager.mark_topic_viewed("Dictionaries")
            
            history = manager.get_session_history()
            # Should have 2 entries (Lists, Dictionaries)
            assert len(history) == 2
    
    def test_clear_session_history(self):
        """Test clearing session history."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(tmpdir)
            manager.mark_topic_viewed("Lists")
            manager.mark_topic_viewed("Dictionaries")
            
            manager.clear_session_history()
            history = manager.get_session_history()
            assert len(history) == 0


class TestSessionManagerPersistence:
    """Test session persistence to disk."""
    
    def test_save_session(self):
        """Test saving session to disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(tmpdir)
            manager.mark_topic_viewed("Lists")
            manager.mark_example_executed("Lists", 1)
            
            success = manager.save_session()
            assert success is True
            assert manager.session_file.exists()
    
    def test_load_session(self):
        """Test loading session from disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create and save a session
            manager1 = SessionManager(tmpdir)
            manager1.mark_topic_viewed("Lists")
            manager1.mark_example_executed("Lists", 1)
            manager1.set_current_topic("Lists")
            manager1.save_session()
            
            # Load the session in a new manager
            manager2 = SessionManager(tmpdir)
            
            viewed = manager2.get_viewed_topics()
            executed = manager2.get_executed_examples()
            current = manager2.get_current_topic()
            
            assert "Lists" in viewed
            assert 1 in executed["Lists"]
            assert current == "Lists"
    
    def test_session_persistence_round_trip(self):
        """Test that session state survives save/load cycle."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create initial session
            manager1 = SessionManager(tmpdir)
            manager1.mark_topic_viewed("Lists")
            manager1.mark_topic_viewed("Dictionaries")
            manager1.mark_example_executed("Lists", 1)
            manager1.mark_example_executed("Lists", 2)
            manager1.mark_example_executed("Dictionaries", 1)
            manager1.set_current_topic("Dictionaries")
            manager1.save_session()
            
            # Load and verify
            manager2 = SessionManager(tmpdir)
            
            assert manager2.get_viewed_topics() == ["Lists", "Dictionaries"]
            assert manager2.get_executed_examples() == {
                "Lists": [1, 2],
                "Dictionaries": [1]
            }
            assert manager2.get_current_topic() == "Dictionaries"


class TestSessionManagerReset:
    """Test progress reset functionality."""
    
    def test_reset_progress(self):
        """Test resetting all progress."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(tmpdir)
            manager.mark_topic_viewed("Lists")
            manager.mark_example_executed("Lists", 1)
            manager.set_current_topic("Lists")
            
            manager.reset_progress()
            
            assert len(manager.get_viewed_topics()) == 0
            assert len(manager.get_executed_examples()) == 0
            assert manager.get_current_topic() is None


class TestSessionManagerUtilityMethods:
    """Test utility methods."""
    
    def test_is_topic_viewed(self):
        """Test checking if topic is viewed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(tmpdir)
            manager.mark_topic_viewed("Lists")
            
            assert manager.is_topic_viewed("Lists") is True
            assert manager.is_topic_viewed("Dictionaries") is False
    
    def test_is_example_executed(self):
        """Test checking if example is executed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(tmpdir)
            manager.mark_example_executed("Lists", 1)
            
            assert manager.is_example_executed("Lists", 1) is True
            assert manager.is_example_executed("Lists", 2) is False
            assert manager.is_example_executed("Dictionaries", 1) is False
    
    def test_get_examples_executed_for_topic(self):
        """Test getting executed examples for a topic."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(tmpdir)
            manager.mark_example_executed("Lists", 1)
            manager.mark_example_executed("Lists", 3)
            
            examples = manager.get_examples_executed_for_topic("Lists")
            assert 1 in examples
            assert 3 in examples
            assert 2 not in examples
    
    def test_get_session_info(self):
        """Test getting session information."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(tmpdir)
            manager.mark_topic_viewed("Lists")
            manager.mark_example_executed("Lists", 1)
            manager.set_current_topic("Lists")
            
            info = manager.get_session_info()
            
            assert info["current_topic"] == "Lists"
            assert info["topics_viewed"] == 1
            assert info["examples_executed"] == 1
            assert "session_duration_seconds" in info
            assert "created_at" in info
            assert "last_updated" in info
