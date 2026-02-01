"""
Unit tests for the REPLEngine class.
"""

import pytest
import tempfile
from unittest.mock import patch, MagicMock
from fishertools.learn.knowledge_engine import KnowledgeEngine
from fishertools.learn.repl.engine import REPLEngine
from fishertools.learn.repl.session_manager import SessionManager


@pytest.fixture
def engine():
    """Fixture to provide a Knowledge Engine instance."""
    return KnowledgeEngine()


@pytest.fixture
def session_manager():
    """Fixture to provide a SessionManager instance."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield SessionManager(tmpdir)


@pytest.fixture
def repl_engine(engine, session_manager):
    """Fixture to provide a REPLEngine instance."""
    return REPLEngine(engine, session_manager)


class TestREPLEngineInitialization:
    """Test REPL engine initialization."""
    
    def test_create_repl_engine(self, repl_engine):
        """Test creating a REPL engine."""
        assert repl_engine is not None
        assert repl_engine.engine is not None
        assert repl_engine.session_manager is not None
        assert repl_engine.command_handler is not None
        assert repl_engine.code_sandbox is not None
    
    def test_repl_engine_default_initialization(self):
        """Test REPL engine with default initialization."""
        engine = REPLEngine()
        assert engine.engine is not None
        assert engine.session_manager is not None


class TestREPLEngineTopicDisplay:
        assert engine.engine is not None
        assert engine.session_manager is not None


class TestREPLEngineTopicDisplay:
    """Test topic display functionality."""
    
    def test_display_topic_sets_current_topic(self, repl_engine, engine):
        """Test that displaying a topic sets current topic."""
        topics = engine.list_topics()
        if topics:
            repl_engine._display_topic(topics[0])
            assert repl_engine.current_topic == topics[0]
    
    def test_display_topic_marks_viewed(self, repl_engine, engine, session_manager):
        """Test that displaying a topic marks it as viewed."""
        topics = engine.list_topics()
        if topics:
            repl_engine._display_topic(topics[0])
            assert session_manager.is_topic_viewed(topics[0])


class TestREPLEngineNavigation:
    """Test navigation functionality."""
    
    def test_navigate_next_from_first_topic(self, repl_engine, engine):
        """Test navigating to next topic from first topic."""
        path = engine.get_learning_path()
        if len(path) > 1:
            repl_engine._display_topic(path[0])
            repl_engine._navigate_next()
            assert repl_engine.current_topic == path[1]
    
    def test_navigate_prev_from_second_topic(self, repl_engine, engine):
        """Test navigating to previous topic from second topic."""
        path = engine.get_learning_path()
        if len(path) > 1:
            repl_engine._display_topic(path[1])
            repl_engine._navigate_prev()
            assert repl_engine.current_topic == path[0]
    
    def test_navigate_to_topic(self, repl_engine, engine):
        """Test navigating to a specific topic."""
        topics = engine.list_topics()
        if topics:
            repl_engine._navigate_to_topic(topics[0])
            assert repl_engine.current_topic == topics[0]


class TestREPLEngineCodeExecution:
    """Test code execution functionality."""
    
    def test_run_example_marks_executed(self, repl_engine, engine, session_manager):
        """Test that running an example marks it as executed."""
        topics = engine.list_topics()
        if topics:
            topic = engine.get_topic(topics[0])
            examples = topic.get("examples", [])
            if examples:
                repl_engine._display_topic(topics[0])
                repl_engine._run_example(1)
                assert session_manager.is_example_executed(topics[0], 1)
    
    def test_run_invalid_example_number(self, repl_engine, engine):
        """Test running an invalid example number."""
        topics = engine.list_topics()
        if topics:
            repl_engine._display_topic(topics[0])
            # Should not crash with invalid example number
            repl_engine._run_example(999)


class TestREPLEngineEditMode:
    """Test edit mode functionality."""
    
    def test_enter_edit_mode(self, repl_engine, engine):
        """Test entering edit mode."""
        topics = engine.list_topics()
        if topics:
            topic = engine.get_topic(topics[0])
            examples = topic.get("examples", [])
            if examples:
                repl_engine._display_topic(topics[0])
                repl_engine._enter_edit_mode(1)
                assert repl_engine.in_edit_mode is True
                assert repl_engine.edit_topic == topics[0]
                assert repl_engine.edit_example_num == 1
    
    def test_exit_edit_mode(self, repl_engine, engine):
        """Test exiting edit mode."""
        topics = engine.list_topics()
        if topics:
            topic = engine.get_topic(topics[0])
            examples = topic.get("examples", [])
            if examples:
                repl_engine._display_topic(topics[0])
                repl_engine._enter_edit_mode(1)
                repl_engine._exit_edit_mode()
                assert repl_engine.in_edit_mode is False


class TestREPLEngineCommandHandling:
    """Test command handling."""
    
    def test_handle_list_command(self, repl_engine):
        """Test handling /list command."""
        # Should not crash
        repl_engine._handle_command(["list"])
    
    def test_handle_help_command(self, repl_engine):
        """Test handling /help command."""
        # Should not crash
        repl_engine._handle_command(["help"])
    
    def test_handle_progress_command(self, repl_engine):
        """Test handling /progress command."""
        # Should not crash
        repl_engine._handle_command(["progress"])
    
    def test_handle_exit_command(self, repl_engine):
        """Test handling /exit command."""
        repl_engine._handle_command(["exit"])
        assert repl_engine.running is False


class TestREPLEngineInputProcessing:
    """Test input processing."""
    
    def test_process_command_input(self, repl_engine):
        """Test processing command input."""
        # Should not crash
        repl_engine._process_input("/help")
    
    def test_process_topic_input(self, repl_engine, engine):
        """Test processing topic input."""
        topics = engine.list_topics()
        if topics:
            # Should not crash
            repl_engine._process_input(topics[0])
    
    def test_process_invalid_input(self, repl_engine):
        """Test processing invalid input."""
        # Should not crash
        repl_engine._process_input("/invalid_command_xyz")
