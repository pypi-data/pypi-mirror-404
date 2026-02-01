"""
Session manager for tracking learning progress and session state.

This module handles tracking viewed topics, executed examples, and persisting
session state to disk for resuming learning sessions.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from fishertools.learn.repl.models import SessionState, ProgressStats


class SessionManager:
    """
    Manages learning progress and session state for the REPL.
    
    Tracks:
    - Viewed topics
    - Executed examples
    - Session history
    - Learning statistics
    
    Persists state to JSON files for resuming sessions.
    
    Example:
        >>> manager = SessionManager()
        >>> manager.mark_topic_viewed("Lists")
        >>> manager.mark_example_executed("Lists", 1)
        >>> stats = manager.get_progress()
        >>> manager.save_session()
    """
    
    DEFAULT_SESSION_FILE = ".repl_session.json"
    DEFAULT_PROGRESS_FILE = ".repl_progress.json"
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize the session manager.
        
        Args:
            storage_path: Optional path to store session files. 
                         Defaults to user's home directory.
        """
        if storage_path is None:
            storage_path = str(Path.home())
        
        self.storage_path = Path(storage_path)
        self.session_file = self.storage_path / self.DEFAULT_SESSION_FILE
        self.progress_file = self.storage_path / self.DEFAULT_PROGRESS_FILE
        
        # Initialize session state
        self.state = SessionState()
        self.session_start_time = datetime.now()
        
        # Load existing session if available
        self.load_session()
    
    def mark_topic_viewed(self, topic_name: str) -> None:
        """
        Mark a topic as viewed.
        
        Args:
            topic_name: Name of the topic to mark as viewed
        """
        if topic_name not in self.state.viewed_topics:
            self.state.viewed_topics.append(topic_name)
        
        # Add to session history
        if not self.state.session_history or self.state.session_history[-1] != topic_name:
            self.state.session_history.append(topic_name)
        
        self.state.last_updated = datetime.now()
    
    def mark_example_executed(self, topic_name: str, example_num: int) -> None:
        """
        Mark an example as executed.
        
        Args:
            topic_name: Name of the topic
            example_num: Number of the example
        """
        if topic_name not in self.state.executed_examples:
            self.state.executed_examples[topic_name] = []
        
        if example_num not in self.state.executed_examples[topic_name]:
            self.state.executed_examples[topic_name].append(example_num)
        
        self.state.last_updated = datetime.now()
    
    def get_progress(self) -> ProgressStats:
        """
        Get current learning progress statistics.
        
        Returns:
            ProgressStats object with current statistics
        """
        # Calculate statistics
        total_topics = len(self.state.viewed_topics)
        viewed_topics = len(self.state.viewed_topics)
        
        total_examples = sum(len(examples) for examples in self.state.executed_examples.values())
        executed_examples = total_examples
        
        # Calculate session duration
        session_duration = (datetime.now() - self.session_start_time).total_seconds()
        
        return ProgressStats(
            total_topics=total_topics,
            viewed_topics=viewed_topics,
            total_examples=total_examples,
            executed_examples=executed_examples,
            categories_explored={},
            difficulty_distribution={},
            session_duration=session_duration,
            last_viewed_topic=self.state.current_topic,
        )
    
    def get_viewed_topics(self) -> List[str]:
        """
        Get list of viewed topics.
        
        Returns:
            List of topic names that have been viewed
        """
        return self.state.viewed_topics.copy()
    
    def get_executed_examples(self) -> Dict[str, List[int]]:
        """
        Get dictionary of executed examples by topic.
        
        Returns:
            Dictionary mapping topic names to lists of executed example numbers
        """
        return {k: v.copy() for k, v in self.state.executed_examples.items()}
    
    def set_current_topic(self, topic_name: str) -> None:
        """
        Set the current topic.
        
        Args:
            topic_name: Name of the current topic
        """
        self.state.current_topic = topic_name
        self.state.last_updated = datetime.now()
    
    def get_current_topic(self) -> Optional[str]:
        """
        Get the current topic.
        
        Returns:
            Name of the current topic or None if not set
        """
        return self.state.current_topic
    
    def get_session_history(self) -> List[str]:
        """
        Get history of viewed topics in current session.
        
        Returns:
            List of topic names in order they were viewed
        """
        return self.state.session_history.copy()
    
    def save_session(self) -> bool:
        """
        Save session state to persistent storage.
        
        Returns:
            True if save was successful, False otherwise
        """
        try:
            # Ensure storage directory exists
            self.storage_path.mkdir(parents=True, exist_ok=True)
            
            # Save session state
            session_data = self.state.to_dict()
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, default=str)
            
            return True
        except Exception as e:
            print(f"Warning: Could not save session: {e}")
            return False
    
    def load_session(self) -> bool:
        """
        Load session state from persistent storage.
        
        Returns:
            True if load was successful, False otherwise
        """
        try:
            if not self.session_file.exists():
                return False
            
            with open(self.session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            self.state = SessionState.from_dict(session_data)
            self.session_start_time = datetime.now()
            return True
        except Exception as e:
            print(f"Warning: Could not load session: {e}")
            return False
    
    def reset_progress(self) -> None:
        """
        Reset all learning progress.
        
        Clears viewed topics, executed examples, and session history.
        """
        self.state = SessionState()
        self.session_start_time = datetime.now()
    
    def clear_session_history(self) -> None:
        """
        Clear the session history.
        
        Keeps viewed topics and executed examples but clears the history.
        """
        self.state.session_history = []
        self.state.last_updated = datetime.now()
    
    def get_session_info(self) -> Dict[str, Any]:
        """
        Get information about the current session.
        
        Returns:
            Dictionary with session information
        """
        session_duration = (datetime.now() - self.session_start_time).total_seconds()
        
        return {
            "current_topic": self.state.current_topic,
            "topics_viewed": len(self.state.viewed_topics),
            "examples_executed": sum(len(ex) for ex in self.state.executed_examples.values()),
            "session_duration_seconds": session_duration,
            "session_history_length": len(self.state.session_history),
            "created_at": self.state.created_at.isoformat(),
            "last_updated": self.state.last_updated.isoformat(),
        }
    
    def is_topic_viewed(self, topic_name: str) -> bool:
        """
        Check if a topic has been viewed.
        
        Args:
            topic_name: Name of the topic
        
        Returns:
            True if topic has been viewed, False otherwise
        """
        return topic_name in self.state.viewed_topics
    
    def is_example_executed(self, topic_name: str, example_num: int) -> bool:
        """
        Check if an example has been executed.
        
        Args:
            topic_name: Name of the topic
            example_num: Number of the example
        
        Returns:
            True if example has been executed, False otherwise
        """
        if topic_name not in self.state.executed_examples:
            return False
        return example_num in self.state.executed_examples[topic_name]
    
    def get_examples_executed_for_topic(self, topic_name: str) -> List[int]:
        """
        Get list of executed examples for a topic.
        
        Args:
            topic_name: Name of the topic
        
        Returns:
            List of executed example numbers
        """
        return self.state.executed_examples.get(topic_name, []).copy()
