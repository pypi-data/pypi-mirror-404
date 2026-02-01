"""
Knowledge Engine for fishertools - Educational system for Python concepts.

This module provides a structured knowledge base of Python concepts for beginners,
with explanations, examples, common mistakes, and related topics.
"""

import json
import os
import random
from typing import Dict, List, Optional


class KnowledgeEngine:
    """
    Knowledge Engine for managing and accessing educational content about Python concepts.
    
    The engine loads topics from a JSON file and provides methods to search, filter,
    and retrieve information about Python concepts for beginners.
    
    Attributes:
        topics (Dict[str, Dict]): Dictionary of all loaded topics indexed by name
        categories (Dict[str, List[str]]): Dictionary mapping categories to topic names
    
    Example:
        >>> engine = KnowledgeEngine()
        >>> topic = engine.get_topic("Lists")
        >>> print(topic["description"])
        >>> all_topics = engine.list_topics()
        >>> related = engine.get_related_topics("Lists")
    """
    
    def __init__(self, topics_file: Optional[str] = None):
        """
        Initialize the Knowledge Engine by loading topics from a JSON file.
        
        Args:
            topics_file: Path to the JSON file containing topics. If None, uses default location.
        
        Raises:
            FileNotFoundError: If the topics file is not found
            ValueError: If the JSON file is invalid or corrupted
        
        Example:
            >>> engine = KnowledgeEngine()
            >>> engine = KnowledgeEngine("custom_topics.json")
        """
        if topics_file is None:
            # Use default location relative to this file
            topics_file = os.path.join(os.path.dirname(__file__), "topics.json")
        
        if not os.path.exists(topics_file):
            raise FileNotFoundError(f"Topics file not found: {topics_file}")
        
        try:
            with open(topics_file, 'r', encoding='utf-8') as f:
                topics_list = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in topics file: {e}")
        
        # Index topics by name for fast lookup
        self.topics: Dict[str, Dict] = {}
        self.categories: Dict[str, List[str]] = {}
        
        for topic in topics_list:
            topic_name = topic.get("topic")
            if not topic_name:
                raise ValueError("Topic missing 'topic' field")
            
            self.topics[topic_name] = topic
            
            # Index by category
            category = topic.get("category", "Uncategorized")
            if category not in self.categories:
                self.categories[category] = []
            self.categories[category].append(topic_name)
    
    def get_topic(self, name: str) -> Optional[Dict]:
        """
        Get a topic by name.
        
        Args:
            name: The name of the topic to retrieve
        
        Returns:
            Dictionary containing the topic information, or None if not found
        
        Example:
            >>> engine = KnowledgeEngine()
            >>> topic = engine.get_topic("Lists")
            >>> if topic:
            ...     print(topic["description"])
        """
        return self.topics.get(name)
    
    def list_topics(self) -> List[str]:
        """
        Get a list of all available topics.
        
        Returns:
            Sorted list of all topic names
        
        Example:
            >>> engine = KnowledgeEngine()
            >>> topics = engine.list_topics()
            >>> print(f"Available topics: {len(topics)}")
        """
        return sorted(self.topics.keys())
    
    def search_topics(self, keyword: str) -> List[str]:
        """
        Search for topics containing a keyword in name or description.
        
        The search is case-insensitive and matches partial words.
        
        Args:
            keyword: The keyword to search for
        
        Returns:
            List of topic names matching the keyword
        
        Example:
            >>> engine = KnowledgeEngine()
            >>> results = engine.search_topics("list")
            >>> print(f"Found {len(results)} topics about lists")
        """
        keyword_lower = keyword.lower()
        results = []
        
        for name, topic in self.topics.items():
            # Search in topic name
            if keyword_lower in name.lower():
                results.append(name)
                continue
            
            # Search in description
            description = topic.get("description", "").lower()
            if keyword_lower in description:
                results.append(name)
                continue
            
            # Search in when_to_use
            when_to_use = topic.get("when_to_use", "").lower()
            if keyword_lower in when_to_use:
                results.append(name)
        
        return sorted(results)
    
    def get_random_topic(self) -> Dict:
        """
        Get a random topic for learning.
        
        Returns:
            A randomly selected topic dictionary
        
        Example:
            >>> engine = KnowledgeEngine()
            >>> topic = engine.get_random_topic()
            >>> print(f"Today's topic: {topic['topic']}")
        """
        topic_name = random.choice(list(self.topics.keys()))
        return self.topics[topic_name]
    
    def get_related_topics(self, topic_name: str) -> List[str]:
        """
        Get topics related to a given topic.
        
        Args:
            topic_name: The name of the topic
        
        Returns:
            List of related topic names that exist in the knowledge base
        
        Example:
            >>> engine = KnowledgeEngine()
            >>> related = engine.get_related_topics("Lists")
            >>> print(f"Related topics: {related}")
        """
        topic = self.get_topic(topic_name)
        if not topic:
            return []
        
        related = topic.get("related_topics", [])
        # Filter to only include topics that exist in the knowledge base
        return [t for t in related if t in self.topics]
    
    def get_topics_by_category(self, category: str) -> List[str]:
        """
        Get all topics in a specific category.
        
        Args:
            category: The category name
        
        Returns:
            Sorted list of topic names in the category
        
        Example:
            >>> engine = KnowledgeEngine()
            >>> basic_types = engine.get_topics_by_category("Basic Types")
            >>> print(f"Topics in Basic Types: {basic_types}")
        """
        return sorted(self.categories.get(category, []))
    
    def get_learning_path(self) -> List[str]:
        """
        Get the recommended learning path from simple to complex topics.
        
        Returns:
            List of topic names ordered by difficulty
        
        Example:
            >>> engine = KnowledgeEngine()
            >>> path = engine.get_learning_path()
            >>> for topic_name in path:
            ...     print(topic_name)
        """
        # Sort topics by order field, then by difficulty
        sorted_topics = sorted(
            self.topics.items(),
            key=lambda x: (x[1].get("order", 999), x[1].get("difficulty", ""))
        )
        return [name for name, _ in sorted_topics]


# Global engine instance
_engine: Optional[KnowledgeEngine] = None


def get_engine() -> KnowledgeEngine:
    """
    Get the global Knowledge Engine instance.
    
    Returns:
        The global KnowledgeEngine instance
    
    Example:
        >>> engine = get_engine()
        >>> topics = engine.list_topics()
    """
    global _engine
    if _engine is None:
        _engine = KnowledgeEngine()
    return _engine


def get_topic(name: str) -> Optional[Dict]:
    """
    Get a topic by name using the global engine.
    
    Args:
        name: The name of the topic
    
    Returns:
        Topic dictionary or None if not found
    
    Example:
        >>> topic = get_topic("Lists")
        >>> if topic:
        ...     print(topic["description"])
    """
    return get_engine().get_topic(name)


def list_topics() -> List[str]:
    """
    Get a list of all available topics using the global engine.
    
    Returns:
        Sorted list of all topic names
    
    Example:
        >>> topics = list_topics()
        >>> print(f"Total topics: {len(topics)}")
    """
    return get_engine().list_topics()


def search_topics(keyword: str) -> List[str]:
    """
    Search for topics by keyword using the global engine.
    
    Args:
        keyword: The keyword to search for
    
    Returns:
        List of matching topic names
    
    Example:
        >>> results = search_topics("loop")
        >>> print(f"Found {len(results)} topics about loops")
    """
    return get_engine().search_topics(keyword)


def get_random_topic() -> Dict:
    """
    Get a random topic using the global engine.
    
    Returns:
        A randomly selected topic dictionary
    
    Example:
        >>> topic = get_random_topic()
        >>> print(f"Random topic: {topic['topic']}")
    """
    return get_engine().get_random_topic()


def get_learning_path() -> List[str]:
    """
    Get the recommended learning path using the global engine.
    
    Returns:
        List of topic names ordered by difficulty
    
    Example:
        >>> path = get_learning_path()
        >>> for topic_name in path[:5]:
        ...     print(topic_name)
    """
    return get_engine().get_learning_path()
