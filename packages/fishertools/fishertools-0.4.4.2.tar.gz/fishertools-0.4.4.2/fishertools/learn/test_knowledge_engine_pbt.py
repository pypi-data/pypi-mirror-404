"""
Property-based tests for the Knowledge Engine module using Hypothesis.

**Validates: Requirements 1.2-1.5, 4.1, 4.3, 5.1, 5.2**
"""

import pytest
from hypothesis import given, strategies as st
from fishertools.learn.knowledge_engine import KnowledgeEngine


@pytest.fixture
def engine():
    """Create a KnowledgeEngine instance for testing."""
    return KnowledgeEngine()


class TestProperty1GetTopicStructure:
    """Property 1: get_topic returns correct structure
    
    **Validates: Requirements 1.2, 2.1**
    """
    
    @given(st.sampled_from(["Lists", "Variables and Assignment", "For Loops"]))
    def test_get_topic_returns_dict_with_required_fields(self, topic_name):
        """For any existing topic, get_topic returns dict with all required fields."""
        engine = KnowledgeEngine()
        topic = engine.get_topic(topic_name)
        
        assert topic is not None
        assert isinstance(topic, dict)
        assert "topic" in topic
        assert "description" in topic
        assert "when_to_use" in topic
        assert "example" in topic
        assert "common_mistakes" in topic
        assert "related_topics" in topic


class TestProperty2ListTopicsComplete:
    """Property 2: list_topics returns all topics
    
    **Validates: Requirements 1.4**
    """
    
    def test_list_topics_returns_all_loaded_topics(self):
        """For any Knowledge Engine, list_topics returns all loaded topics."""
        engine = KnowledgeEngine()
        topics_list = engine.list_topics()
        
        # Should have exactly 35 topics
        assert len(topics_list) == 35
        
        # All topics should be strings
        assert all(isinstance(t, str) for t in topics_list)
        
        # All topics should be retrievable
        for topic_name in topics_list:
            assert engine.get_topic(topic_name) is not None


class TestProperty3SearchTopicsRelevant:
    """Property 3: search_topics finds relevant topics
    
    **Validates: Requirements 1.5**
    """
    
    @given(st.sampled_from(["list", "loop", "function", "string", "error"]))
    def test_search_topics_returns_only_relevant(self, keyword):
        """For any keyword, search_topics returns only topics containing that keyword."""
        engine = KnowledgeEngine()
        results = engine.search_topics(keyword)
        
        # All results should contain the keyword (case-insensitive)
        for topic_name in results:
            topic = engine.get_topic(topic_name)
            full_text = (
                topic["topic"].lower() +
                topic["description"].lower() +
                topic["when_to_use"].lower()
            )
            assert keyword.lower() in full_text


class TestProperty4RelatedTopicsExist:
    """Property 4: get_related_topics returns existing topics
    
    **Validates: Requirements 1.5**
    """
    
    @given(st.sampled_from(["Lists", "Variables and Assignment", "For Loops", "Functions"]))
    def test_related_topics_all_exist(self, topic_name):
        """For any topic, all related topics exist in the knowledge base."""
        engine = KnowledgeEngine()
        related = engine.get_related_topics(topic_name)
        
        # All related topics should exist
        for related_name in related:
            assert engine.get_topic(related_name) is not None


class TestProperty5ExamplesValid:
    """Property 5: examples are valid Python code
    
    **Validates: Requirements 5.1, 5.2**
    """
    
    @given(st.sampled_from(["Lists", "Variables and Assignment", "For Loops", "Dictionaries"]))
    def test_examples_are_valid_python(self, topic_name):
        """For any topic, the example is valid Python code."""
        engine = KnowledgeEngine()
        topic = engine.get_topic(topic_name)
        example = topic.get("example", "")
        
        # Should be compilable Python
        try:
            compile(example, f"<example:{topic_name}>", "exec")
        except SyntaxError:
            pytest.fail(f"Example in '{topic_name}' is not valid Python")


class TestProperty6CategoriesConsistent:
    """Property 6: categories are consistent
    
    **Validates: Requirements 4.1**
    """
    
    def test_all_topics_have_valid_category(self):
        """For any topic, the category is one of the valid categories."""
        engine = KnowledgeEngine()
        valid_categories = {
            "Basic Types", "Collections", "Control Flow", "Functions",
            "String Operations", "File Operations", "Error Handling", "Advanced Basics"
        }
        
        for topic_name in engine.list_topics():
            topic = engine.get_topic(topic_name)
            assert topic["category"] in valid_categories


class TestProperty7RelatedTopicsConsistent:
    """Property 7: related_topics contain existing topics
    
    **Validates: Requirements 4.1**
    """
    
    def test_all_related_topics_exist(self):
        """For any topic, all related topics exist in the knowledge base."""
        engine = KnowledgeEngine()
        
        for topic_name in engine.list_topics():
            topic = engine.get_topic(topic_name)
            for related_name in topic.get("related_topics", []):
                assert engine.get_topic(related_name) is not None, \
                    f"Related topic '{related_name}' not found for '{topic_name}'"


class TestProperty8LearningPathOrdered:
    """Property 8: get_learning_path returns topics in correct order
    
    **Validates: Requirements 4.3**
    """
    
    def test_learning_path_ordered_by_difficulty(self):
        """For any Knowledge Engine, learning path is ordered from simple to complex."""
        engine = KnowledgeEngine()
        path = engine.get_learning_path()
        
        # Should have all 35 topics
        assert len(path) == 35
        
        # Should be ordered by order field
        for i in range(len(path) - 1):
            current_topic = engine.get_topic(path[i])
            next_topic = engine.get_topic(path[i + 1])
            assert current_topic["order"] <= next_topic["order"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
