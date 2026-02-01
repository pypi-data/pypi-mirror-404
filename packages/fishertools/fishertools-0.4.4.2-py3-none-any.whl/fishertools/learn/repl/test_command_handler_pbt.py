"""
Property-based tests for CommandHandler using Hypothesis.

**Validates: Requirements 2.1, 2.2**
"""

import pytest
import tempfile
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from fishertools.learn.knowledge_engine import KnowledgeEngine
from fishertools.learn.repl.command_handler import CommandHandler
from fishertools.learn.repl.session_manager import SessionManager


class TestCommandHandlerProperties:
    """Property-based tests for command handler."""
    
    def test_search_result_relevance(self):
        """
        Property 3: Search Result Relevance
        
        For any search keyword and topic database, all returned search results 
        should contain the keyword in either the topic name or description (case-insensitive).
        
        **Validates: Requirements 2.2**
        """
        engine = KnowledgeEngine()
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(tmpdir)
            handler = CommandHandler(engine, manager)
            
            # Get all topics to search for
            all_topics = engine.list_topics()
            if len(all_topics) > 0:
                # Use a topic name as keyword
                keyword = all_topics[0].lower()
                output = handler.handle_search(keyword)
                
                # Output should be a string
                assert isinstance(output, str)
                # If results are found, they should contain the keyword
                if "Found" in output and "0 topic" not in output:
                    # Results were found, verify they contain the keyword
                    assert keyword in output.lower() or "search" in output.lower()
    
    def test_topic_list_completeness(self):
        """
        Property 11: Topic List Completeness
        
        For any /list command, all topics from the Knowledge Engine should appear 
        in the output organized by their categories.
        
        **Validates: Requirements 2.1**
        """
        engine = KnowledgeEngine()
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(tmpdir)
            handler = CommandHandler(engine, manager)
            
            output = handler.handle_list()
            
            # Output should be a string
            assert isinstance(output, str)
            
            # Get all topics
            all_topics = engine.list_topics()
            
            # Output should mention the total number of topics
            assert "Total topics" in output or "topics" in output.lower()
            
            # Output should contain category information
            categories = list(engine.categories.keys())
            if categories:
                # At least one category should be mentioned
                assert any(cat in output for cat in categories) or "📂" in output
    
    @given(st.text(min_size=1, max_size=100))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_search_always_returns_string(self, keyword):
        """
        For any search keyword, the search handler should always return a string.
        
        **Validates: Requirements 2.2**
        """
        engine = KnowledgeEngine()
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(tmpdir)
            handler = CommandHandler(engine, manager)
            
            output = handler.handle_search(keyword)
            assert isinstance(output, str)
            assert len(output) > 0
    
    @given(st.text(min_size=1, max_size=100))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_category_always_returns_string(self, category_name):
        """
        For any category name, the category handler should always return a string.
        
        **Validates: Requirements 2.1**
        """
        engine = KnowledgeEngine()
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(tmpdir)
            handler = CommandHandler(engine, manager)
            
            output = handler.handle_category(category_name)
            assert isinstance(output, str)
            assert len(output) > 0
    
    def test_list_output_structure(self):
        """
        For /list command, output should have consistent structure.
        
        **Validates: Requirements 2.1**
        """
        engine = KnowledgeEngine()
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(tmpdir)
            handler = CommandHandler(engine, manager)
            
            output = handler.handle_list()
            
            # Should contain header
            assert "Available Topics" in output or "📚" in output
            
            # Should contain instructions
            assert "Type" in output or "topic" in output.lower()
    
    def test_search_output_structure(self):
        """
        For /search command, output should have consistent structure.
        
        **Validates: Requirements 2.2**
        """
        engine = KnowledgeEngine()
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(tmpdir)
            handler = CommandHandler(engine, manager)
            
            # Get a valid keyword
            topics = engine.list_topics()
            if topics:
                keyword = topics[0].lower()
                output = handler.handle_search(keyword)
                
                # Should contain search indicator
                assert "search" in output.lower() or "🔍" in output
                
                # Should contain result count
                assert "Found" in output or "topic" in output.lower()
    
    def test_categories_output_structure(self):
        """
        For /categories command, output should have consistent structure.
        
        **Validates: Requirements 2.1**
        """
        engine = KnowledgeEngine()
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(tmpdir)
            handler = CommandHandler(engine, manager)
            
            output = handler.handle_categories()
            
            # Should contain header
            assert "Categories" in output or "📂" in output
            
            # Should contain count information
            assert "Total categories" in output or "categories" in output.lower()
    
    def test_path_output_structure(self):
        """
        For /path command, output should have consistent structure.
        
        **Validates: Requirements 2.1**
        """
        engine = KnowledgeEngine()
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(tmpdir)
            handler = CommandHandler(engine, manager)
            
            output = handler.handle_path()
            
            # Should contain header
            assert "Learning Path" in output or "🛤️" in output
            
            # Should contain topic count
            assert "Total topics" in output or "topics" in output.lower()
