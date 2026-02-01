"""
Progress tracking system for learning activities.
"""

import json
import os
from typing import List, Optional, Dict
from datetime import datetime
from .models import LearningProgress, DifficultyLevel


class ProgressSystem:
    """
    Tracks user learning progress and manages achievements.
    
    Provides persistent progress tracking between sessions and
    suggests appropriate next steps based on completion status.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize the progress system.
        
        Args:
            storage_path: Optional path for persistent storage
        """
        self.storage_path = storage_path or os.path.expanduser("~/.fishertools_progress")
        self._progress_data: Dict[str, LearningProgress] = {}
        
        # Topic progression paths
        self._topic_progression = {
            "beginner": [
                "variables", "data_types", "input_output", "operators",
                "conditionals", "loops", "lists", "functions"
            ],
            "intermediate": [
                "dictionaries", "file_operations", "error_handling", 
                "modules", "classes", "list_comprehensions"
            ],
            "advanced": [
                "decorators", "generators", "context_managers",
                "metaclasses", "async_programming", "testing"
            ]
        }
        
        # Achievement definitions
        self._achievements = {
            "first_steps": "Completed first tutorial",
            "variable_master": "Mastered variables and data types",
            "loop_expert": "Completed all loop exercises",
            "function_guru": "Created 10 functions",
            "error_handler": "Learned error handling",
            "level_up": "Advanced to next difficulty level",
            "persistent_learner": "Studied for 5 consecutive days",
            "completionist": "Finished all beginner topics"
        }
    
    def create_user_profile(self, user_id: str, initial_level: DifficultyLevel = DifficultyLevel.BEGINNER) -> LearningProgress:
        """
        Create a new user progress profile.
        
        Args:
            user_id: Unique identifier for the user
            initial_level: Starting difficulty level
            
        Returns:
            LearningProgress: New progress profile
        """
        if not user_id or not isinstance(user_id, str):
            raise ValueError("User ID must be a non-empty string")
        
        progress = LearningProgress(
            user_id=user_id,
            completed_topics=[],
            current_level=initial_level,
            total_exercises_completed=0,
            last_activity=datetime.now(),
            achievements=[],
            session_count=0,
            total_time_spent=0
        )
        
        self._progress_data[user_id] = progress
        self.save_progress(user_id)
        
        return progress
    
    def update_progress(self, user_id: str, topic: str, completed: bool) -> None:
        """
        Update user progress for a specific topic.
        
        Args:
            user_id: Unique identifier for the user
            topic: Topic that was studied
            completed: Whether the topic was completed successfully
        """
        if not user_id or not isinstance(user_id, str):
            raise ValueError("User ID must be a non-empty string")
        
        if not topic or not isinstance(topic, str):
            raise ValueError("Topic must be a non-empty string")
        
        # Get or create user progress
        progress = self.get_progress(user_id)
        if not progress:
            progress = self.create_user_profile(user_id)
        
        # Update last activity
        progress.last_activity = datetime.now()
        
        # Add topic to completed list if completed and not already there
        if completed and topic not in progress.completed_topics:
            progress.completed_topics.append(topic)
            progress.total_exercises_completed += 1
            
            # Check for achievements
            self._check_achievements(progress, topic)
            
            # Check for level progression
            self._check_level_progression(progress)
        
        self.save_progress(user_id)
    
    def get_progress(self, user_id: str) -> Optional[LearningProgress]:
        """
        Get current progress for a user.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            Optional[LearningProgress]: User's progress or None if not found
        """
        if not user_id or not isinstance(user_id, str):
            return None
        
        # Try to get from memory first
        if user_id in self._progress_data:
            return self._progress_data[user_id]
        
        # Try to load from storage
        return self.load_progress(user_id)
    
    def suggest_next_topics(self, user_id: str) -> List[str]:
        """
        Suggest appropriate next topics based on user progress.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            List[str]: List of suggested topic names
        """
        progress = self.get_progress(user_id)
        if not progress:
            # Return beginner topics for new users
            return self._topic_progression["beginner"][:3]
        
        level_key = progress.current_level.value
        available_topics = self._topic_progression.get(level_key, [])
        
        # Filter out completed topics
        suggested = [topic for topic in available_topics 
                    if topic not in progress.completed_topics]
        
        # If all topics at current level are completed, suggest next level
        if not suggested and level_key == "beginner":
            suggested = self._topic_progression["intermediate"][:3]
        elif not suggested and level_key == "intermediate":
            suggested = self._topic_progression["advanced"][:3]
        
        return suggested[:5]  # Limit to 5 suggestions
    
    def add_achievement(self, user_id: str, achievement: str) -> None:
        """
        Add an achievement to the user's profile.
        
        Args:
            user_id: Unique identifier for the user
            achievement: Achievement name or description
        """
        progress = self.get_progress(user_id)
        if progress and achievement not in progress.achievements:
            progress.achievements.append(achievement)
            self.save_progress(user_id)
    
    def save_progress(self, user_id: str) -> None:
        """
        Save user progress to persistent storage.
        
        Args:
            user_id: Unique identifier for the user
        """
        progress = self._progress_data.get(user_id)
        if not progress:
            return
        
        try:
            # Ensure storage directory exists
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            
            # Load existing data
            all_progress = {}
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    all_progress = json.load(f)
            
            # Convert progress to serializable format
            progress_dict = {
                "user_id": progress.user_id,
                "completed_topics": progress.completed_topics,
                "current_level": progress.current_level.value,
                "total_exercises_completed": progress.total_exercises_completed,
                "last_activity": progress.last_activity.isoformat(),
                "achievements": progress.achievements,
                "session_count": progress.session_count,
                "total_time_spent": progress.total_time_spent
            }
            
            # Update and save
            all_progress[user_id] = progress_dict
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(all_progress, f, indent=2)
                
        except (OSError, json.JSONEncodeError) as e:
            # Silently fail - progress tracking shouldn't break the system
            pass
    
    def load_progress(self, user_id: str) -> Optional[LearningProgress]:
        """
        Load user progress from persistent storage.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            Optional[LearningProgress]: Loaded progress or None if not found
        """
        try:
            if not os.path.exists(self.storage_path):
                return None
            
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                all_progress = json.load(f)
            
            progress_dict = all_progress.get(user_id)
            if not progress_dict:
                return None
            
            # Convert back to LearningProgress object
            progress = LearningProgress(
                user_id=progress_dict["user_id"],
                completed_topics=progress_dict["completed_topics"],
                current_level=DifficultyLevel(progress_dict["current_level"]),
                total_exercises_completed=progress_dict["total_exercises_completed"],
                last_activity=datetime.fromisoformat(progress_dict["last_activity"]),
                achievements=progress_dict["achievements"],
                session_count=progress_dict.get("session_count", 0),
                total_time_spent=progress_dict.get("total_time_spent", 0)
            )
            
            # Cache in memory
            self._progress_data[user_id] = progress
            return progress
            
        except (OSError, json.JSONDecodeError, KeyError, ValueError):
            # Return None if loading fails
            return None
    
    def _check_achievements(self, progress: LearningProgress, completed_topic: str) -> None:
        """Check and award achievements based on progress."""
        # First tutorial completion
        if len(progress.completed_topics) == 1:
            self.add_achievement(progress.user_id, self._achievements["first_steps"])
        
        # Topic-specific achievements
        if completed_topic == "variables" and "data_types" in progress.completed_topics:
            self.add_achievement(progress.user_id, self._achievements["variable_master"])
        
        if completed_topic in ["for_loops", "while_loops"] and all(
            topic in progress.completed_topics for topic in ["for_loops", "while_loops"]
        ):
            self.add_achievement(progress.user_id, self._achievements["loop_expert"])
        
        if completed_topic == "error_handling":
            self.add_achievement(progress.user_id, self._achievements["error_handler"])
        
        # Milestone achievements
        if progress.total_exercises_completed >= 10:
            self.add_achievement(progress.user_id, self._achievements["function_guru"])
        
        # Check if all beginner topics completed
        beginner_topics = set(self._topic_progression["beginner"])
        completed_topics = set(progress.completed_topics)
        if beginner_topics.issubset(completed_topics):
            self.add_achievement(progress.user_id, self._achievements["completionist"])
    
    def _check_level_progression(self, progress: LearningProgress) -> None:
        """Check if user should advance to next level."""
        current_level = progress.current_level.value
        current_topics = set(self._topic_progression.get(current_level, []))
        completed_topics = set(progress.completed_topics)
        
        # Check if 80% of current level topics are completed
        if len(current_topics) > 0:
            completion_rate = len(current_topics.intersection(completed_topics)) / len(current_topics)
            
            if completion_rate >= 0.8:
                if current_level == "beginner":
                    progress.current_level = DifficultyLevel.INTERMEDIATE
                    self.add_achievement(progress.user_id, self._achievements["level_up"])
                elif current_level == "intermediate":
                    progress.current_level = DifficultyLevel.ADVANCED
                    self.add_achievement(progress.user_id, self._achievements["level_up"])