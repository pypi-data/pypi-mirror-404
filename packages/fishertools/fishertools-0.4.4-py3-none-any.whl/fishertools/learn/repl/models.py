"""
Data models for the Knowledge Engine REPL.

This module defines the core data structures used throughout the REPL system.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Optional, Any


@dataclass
class ExampleDisplay:
    """Represents a code example for display in the REPL."""
    
    number: int
    description: str
    code: str
    expected_output: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExampleDisplay":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class TopicDisplay:
    """Represents a topic with all its information for display."""
    
    name: str
    category: str
    difficulty: str
    description: str
    examples: List[ExampleDisplay] = field(default_factory=list)
    common_mistakes: List[str] = field(default_factory=list)
    related_topics: List[str] = field(default_factory=list)
    tips: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data["examples"] = [ex.to_dict() for ex in self.examples]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TopicDisplay":
        """Create from dictionary."""
        examples = [ExampleDisplay.from_dict(ex) for ex in data.get("examples", [])]
        return cls(
            name=data["name"],
            category=data["category"],
            difficulty=data["difficulty"],
            description=data["description"],
            examples=examples,
            common_mistakes=data.get("common_mistakes", []),
            related_topics=data.get("related_topics", []),
            tips=data.get("tips", []),
        )


@dataclass
class ProgressStats:
    """Statistics about learning progress."""
    
    total_topics: int
    viewed_topics: int
    total_examples: int
    executed_examples: int
    categories_explored: Dict[str, int] = field(default_factory=dict)
    difficulty_distribution: Dict[str, int] = field(default_factory=dict)
    session_duration: float = 0.0
    last_viewed_topic: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProgressStats":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class SessionState:
    """Represents the state of a REPL session."""
    
    current_topic: Optional[str] = None
    viewed_topics: List[str] = field(default_factory=list)
    executed_examples: Dict[str, List[int]] = field(default_factory=dict)
    session_history: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "current_topic": self.current_topic,
            "viewed_topics": self.viewed_topics,
            "executed_examples": self.executed_examples,
            "session_history": self.session_history,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionState":
        """Create from dictionary."""
        return cls(
            current_topic=data.get("current_topic"),
            viewed_topics=data.get("viewed_topics", []),
            executed_examples=data.get("executed_examples", {}),
            session_history=data.get("session_history", []),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            last_updated=datetime.fromisoformat(data["last_updated"]) if "last_updated" in data else datetime.now(),
        )
