"""
Unit tests for the CommandHandler class.
"""

import pytest
import tempfile
from fishertools.learn.knowledge_engine import KnowledgeEngine
from fishertools.learn.repl.command_handler import CommandHandler
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
def handler(engine, session_manager):
    """Fixture to provide a CommandHandler instance."""
    return CommandHandler(engine, session_manager)


class TestCommandHandlerList:
    """Test /list command."""
    
    def test_handle_list_returns_string(self, handler):
        """Test that /list returns a string."""
        output = handler.handle_list()
        assert isinstance(output, str)
        assert len(output) > 0
    
    def test_handle_list_contains_topics(self, handler):
        """Test that /list output contains topics."""
        output = handler.handle_list()
        assert "Available Topics" in output or "📚" in output


class TestCommandHandlerSearch:
    """Test /search command."""
    
    def test_handle_search_empty_keyword(self, handler):
        """Test /search with empty keyword."""
        output = handler.handle_search("")
        assert "Please provide" in output or "keyword" in output.lower()
    
    def test_handle_search_valid_keyword(self, handler, engine):
        """Test /search with valid keyword."""
        # Get a topic to search for
        topics = engine.list_topics()
        if topics:
            keyword = topics[0].lower()
            output = handler.handle_search(keyword)
            assert isinstance(output, str)


class TestCommandHandlerRandom:
    """Test /random command."""
    
    def test_handle_random_returns_string(self, handler):
        """Test that /random returns a string."""
        output = handler.handle_random()
        assert isinstance(output, str)
        assert "Random" in output or "🎲" in output


class TestCommandHandlerCategories:
    """Test /categories command."""
    
    def test_handle_categories_returns_string(self, handler):
        """Test that /categories returns a string."""
        output = handler.handle_categories()
        assert isinstance(output, str)
        assert "Categories" in output or "📂" in output


class TestCommandHandlerCategory:
    """Test /category command."""
    
    def test_handle_category_empty_name(self, handler):
        """Test /category with empty name."""
        output = handler.handle_category("")
        assert "Please provide" in output or "category" in output.lower()
    
    def test_handle_category_valid_name(self, handler, engine):
        """Test /category with valid category name."""
        categories = list(engine.categories.keys())
        if categories:
            output = handler.handle_category(categories[0])
            assert isinstance(output, str)


class TestCommandHandlerPath:
    """Test /path command."""
    
    def test_handle_path_returns_string(self, handler):
        """Test that /path returns a string."""
        output = handler.handle_path()
        assert isinstance(output, str)
        assert "Learning Path" in output or "🛤️" in output


class TestCommandHandlerProgress:
    """Test /progress command."""
    
    def test_handle_progress_returns_string(self, handler):
        """Test that /progress returns a string."""
        output = handler.handle_progress()
        assert isinstance(output, str)
        assert "Progress" in output or "📊" in output
    
    def test_handle_progress_shows_stats(self, handler, session_manager):
        """Test that /progress shows statistics."""
        session_manager.mark_topic_viewed("Lists")
        output = handler.handle_progress()
        assert "Topics viewed" in output or "viewed" in output.lower()


class TestCommandHandlerStats:
    """Test /stats command."""
    
    def test_handle_stats_returns_string(self, handler):
        """Test that /stats returns a string."""
        output = handler.handle_stats()
        assert isinstance(output, str)
        assert "Statistics" in output or "📈" in output


class TestCommandHandlerHelp:
    """Test /help command."""
    
    def test_handle_help_returns_string(self, handler):
        """Test that /help returns a string."""
        output = handler.handle_help()
        assert isinstance(output, str)
        assert "Commands" in output or "help" in output.lower()
    
    def test_handle_help_specific_command(self, handler):
        """Test /help for specific command."""
        output = handler.handle_help("list")
        assert isinstance(output, str)
        assert "list" in output.lower()
    
    def test_handle_help_invalid_command(self, handler):
        """Test /help for invalid command."""
        output = handler.handle_help("invalid_command_xyz")
        assert isinstance(output, str)


class TestCommandHandlerCommands:
    """Test /commands command."""
    
    def test_handle_commands_returns_string(self, handler):
        """Test that /commands returns a string."""
        output = handler.handle_commands()
        assert isinstance(output, str)
        assert "Commands" in output or "📋" in output


class TestCommandHandlerAbout:
    """Test /about command."""
    
    def test_handle_about_returns_string(self, handler):
        """Test that /about returns a string."""
        output = handler.handle_about()
        assert isinstance(output, str)
        assert "About" in output or "ℹ️" in output


class TestCommandHandlerHint:
    """Test /hint command."""
    
    def test_handle_hint_no_topic(self, handler):
        """Test /hint with no current topic."""
        output = handler.handle_hint(None)
        assert "No current topic" in output or "❌" in output
    
    def test_handle_hint_invalid_topic(self, handler):
        """Test /hint with invalid topic."""
        output = handler.handle_hint("NonexistentTopic123")
        assert "not found" in output.lower() or "❌" in output


class TestCommandHandlerTip:
    """Test /tip command."""
    
    def test_handle_tip_returns_string(self, handler):
        """Test that /tip returns a string."""
        output = handler.handle_tip()
        assert isinstance(output, str)
        assert "💡" in output


class TestCommandHandlerRelated:
    """Test /related command."""
    
    def test_handle_related_no_topic(self, handler):
        """Test /related with no current topic."""
        output = handler.handle_related(None)
        assert "No current topic" in output or "❌" in output


class TestCommandHandlerFormatTopic:
    """Test topic formatting."""
    
    def test_format_topic_display_invalid_topic(self, handler):
        """Test formatting invalid topic."""
        output = handler.format_topic_display("NonexistentTopic123")
        assert "not found" in output.lower() or "❌" in output
    
    def test_format_topic_display_valid_topic(self, handler, engine):
        """Test formatting valid topic."""
        topics = engine.list_topics()
        if topics:
            output = handler.format_topic_display(topics[0])
            assert isinstance(output, str)
            assert topics[0] in output
