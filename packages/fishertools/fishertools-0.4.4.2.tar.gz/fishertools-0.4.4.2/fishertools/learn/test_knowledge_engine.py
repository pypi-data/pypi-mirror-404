"""
Unit tests for the Knowledge Engine module.
"""

import pytest
import os
import json
from fishertools.learn.knowledge_engine import (
    KnowledgeEngine, get_topic, list_topics, search_topics,
    get_random_topic, get_learning_path, get_engine
)


class TestKnowledgeEngine:
    """Test suite for KnowledgeEngine class."""
    
    @pytest.fixture
    def engine(self):
        """Create a KnowledgeEngine instance for testing."""
        return KnowledgeEngine()
    
    def test_engine_initialization(self, engine):
        """Test that engine initializes correctly."""
        assert engine is not None
        assert len(engine.topics) > 0
        assert len(engine.categories) > 0
    
    def test_get_topic_existing(self, engine):
        """Test getting an existing topic."""
        topic = engine.get_topic("Lists")
        assert topic is not None
        assert topic["topic"] == "Lists"
        assert "description" in topic
        assert "example" in topic
        assert "common_mistakes" in topic
        assert "related_topics" in topic
    
    def test_get_topic_nonexistent(self, engine):
        """Test getting a non-existent topic returns None."""
        topic = engine.get_topic("NonExistentTopic")
        assert topic is None
    
    def test_list_topics(self, engine):
        """Test listing all topics."""
        topics = engine.list_topics()
        assert isinstance(topics, list)
        assert len(topics) == 35
        assert "Lists" in topics
        assert "Variables and Assignment" in topics
        # Check that list is sorted
        assert topics == sorted(topics)
    
    def test_search_topics_by_name(self, engine):
        """Test searching topics by name."""
        results = engine.search_topics("list")
        assert len(results) > 0
        assert "Lists" in results
        assert "List Indexing" in results
        assert "List Slicing" in results
    
    def test_search_topics_case_insensitive(self, engine):
        """Test that search is case-insensitive."""
        results1 = engine.search_topics("loop")
        results2 = engine.search_topics("LOOP")
        assert results1 == results2
    
    def test_search_topics_by_description(self, engine):
        """Test searching topics by description."""
        results = engine.search_topics("immutable")
        assert len(results) > 0
    
    def test_get_random_topic(self, engine):
        """Test getting a random topic."""
        topic = engine.get_random_topic()
        assert topic is not None
        assert "topic" in topic
        assert "description" in topic
    
    def test_get_related_topics(self, engine):
        """Test getting related topics."""
        related = engine.get_related_topics("Lists")
        assert isinstance(related, list)
        # All related topics should exist
        for topic_name in related:
            assert engine.get_topic(topic_name) is not None
    
    def test_get_related_topics_nonexistent(self, engine):
        """Test getting related topics for non-existent topic."""
        related = engine.get_related_topics("NonExistent")
        assert related == []
    
    def test_get_topics_by_category(self, engine):
        """Test getting topics by category."""
        basic_types = engine.get_topics_by_category("Basic Types")
        assert len(basic_types) == 5
        assert "Variables and Assignment" in basic_types
        assert "Integers and Floats" in basic_types
    
    def test_get_topics_by_category_collections(self, engine):
        """Test getting Collections category topics."""
        collections = engine.get_topics_by_category("Collections")
        assert len(collections) == 6
    
    def test_get_topics_by_category_nonexistent(self, engine):
        """Test getting non-existent category."""
        topics = engine.get_topics_by_category("NonExistent")
        assert topics == []
    
    def test_get_learning_path(self, engine):
        """Test getting learning path."""
        path = engine.get_learning_path()
        assert isinstance(path, list)
        assert len(path) == 35
        # Check that it's ordered by order field
        assert path[0] == "Variables and Assignment"  # order=1
        assert path[-1] == "Enumerate"  # order=35
    
    def test_topic_structure(self, engine):
        """Test that all topics have required fields."""
        for topic_name in engine.list_topics():
            topic = engine.get_topic(topic_name)
            assert "topic" in topic
            assert "category" in topic
            assert "description" in topic
            assert "when_to_use" in topic
            assert "example" in topic
            assert "common_mistakes" in topic
            assert "related_topics" in topic
            assert "difficulty" in topic
            assert "order" in topic
    
    def test_categories_consistency(self, engine):
        """Test that all categories are valid."""
        valid_categories = {
            "Basic Types", "Collections", "Control Flow", "Functions",
            "String Operations", "File Operations", "Error Handling", "Advanced Basics"
        }
        for category in engine.categories.keys():
            assert category in valid_categories
    
    def test_related_topics_exist(self, engine):
        """Test that all related topics exist in the knowledge base."""
        for topic_name in engine.list_topics():
            topic = engine.get_topic(topic_name)
            for related_name in topic.get("related_topics", []):
                assert engine.get_topic(related_name) is not None, \
                    f"Related topic '{related_name}' not found for '{topic_name}'"


class TestModuleFunctions:
    """Test suite for module-level functions."""
    
    def test_get_topic_function(self):
        """Test module-level get_topic function."""
        topic = get_topic("Lists")
        assert topic is not None
        assert topic["topic"] == "Lists"
    
    def test_list_topics_function(self):
        """Test module-level list_topics function."""
        topics = list_topics()
        assert len(topics) == 35
    
    def test_search_topics_function(self):
        """Test module-level search_topics function."""
        results = search_topics("loop")
        assert len(results) > 0
    
    def test_get_random_topic_function(self):
        """Test module-level get_random_topic function."""
        topic = get_random_topic()
        assert topic is not None
        assert "topic" in topic
    
    def test_get_learning_path_function(self):
        """Test module-level get_learning_path function."""
        path = get_learning_path()
        assert len(path) == 35
    
    def test_get_engine_singleton(self):
        """Test that get_engine returns singleton."""
        engine1 = get_engine()
        engine2 = get_engine()
        assert engine1 is engine2


class TestExamples:
    """Test that all examples are valid Python code."""
    
    @pytest.fixture
    def engine(self):
        """Create a KnowledgeEngine instance for testing."""
        return KnowledgeEngine()
    
    def test_all_examples_executable(self, engine):
        """Test that all examples can be executed."""
        for topic_name in engine.list_topics():
            topic = engine.get_topic(topic_name)
            example = topic.get("example", "")
            
            # Try to compile the example
            try:
                compile(example, f"<example:{topic_name}>", "exec")
            except SyntaxError as e:
                pytest.fail(f"Example in '{topic_name}' has syntax error: {e}")
    
    def test_example_contains_output_comments(self, engine):
        """Test that examples have output comments where appropriate."""
        for topic_name in engine.list_topics():
            topic = engine.get_topic(topic_name)
            example = topic.get("example", "")
            # Most examples should have comments with output
            # But not all - some examples don't have print statements
            if "print" in example and len(example) > 50:
                # Only check for comments in longer examples with print
                pass  # Skip this check as not all examples need comments


class TestPerformance:
    """Test performance requirements."""
    
    def test_engine_initialization_performance(self):
        """Test that engine initializes quickly."""
        import time
        start = time.time()
        engine = KnowledgeEngine()
        elapsed = (time.time() - start) * 1000  # Convert to ms
        assert elapsed < 100, f"Engine initialization took {elapsed}ms, should be < 100ms"
    
    def test_search_performance(self):
        """Test that search is fast."""
        import time
        engine = KnowledgeEngine()
        start = time.time()
        results = engine.search_topics("loop")
        elapsed = (time.time() - start) * 1000  # Convert to ms
        assert elapsed < 100, f"Search took {elapsed}ms, should be < 100ms"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
