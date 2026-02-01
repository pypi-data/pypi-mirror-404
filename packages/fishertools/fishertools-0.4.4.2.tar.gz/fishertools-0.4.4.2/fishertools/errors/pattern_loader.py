"""
Pattern loader for error explanation system.

This module handles loading and validation of error patterns,
separating concerns from the main ErrorExplainer class.
"""

from typing import List
from .models import ErrorPattern
from .patterns import load_default_patterns
from .exceptions import ExplanationError


class PatternLoader:
    """
    Handles loading of error patterns.
    
    Responsibilities:
    - Load patterns from various sources
    - Cache loaded patterns
    - Provide pattern access
    """
    
    def __init__(self):
        """Initialize pattern loader."""
        self._patterns_cache: List[ErrorPattern] = []
        self._loaded = False
    
    def load_patterns(self) -> List[ErrorPattern]:
        """
        Load error patterns for matching exceptions.
        
        Returns:
            List of ErrorPattern objects
            
        Raises:
            ExplanationError: If patterns cannot be loaded
        """
        if self._loaded:
            return self._patterns_cache
        
        try:
            self._patterns_cache = load_default_patterns()
            self._loaded = True
            return self._patterns_cache
        except Exception as e:
            raise ExplanationError(
                f"Не удалось загрузить паттерны ошибок: {e}",
                original_error=e
            )
    
    def get_patterns(self) -> List[ErrorPattern]:
        """
        Get loaded patterns (loads if not already loaded).
        
        Returns:
            List of ErrorPattern objects
        """
        if not self._loaded:
            return self.load_patterns()
        return self._patterns_cache
    
    def reload_patterns(self) -> List[ErrorPattern]:
        """
        Force reload of patterns.
        
        Returns:
            List of ErrorPattern objects
        """
        self._loaded = False
        return self.load_patterns()


class PatternMatcher:
    """
    Handles pattern matching logic.
    
    Responsibilities:
    - Match exceptions to patterns
    - Rank pattern matches
    - Handle matching errors gracefully
    """
    
    def __init__(self, patterns: List[ErrorPattern]):
        """
        Initialize pattern matcher.
        
        Args:
            patterns: List of patterns to match against
        """
        self.patterns = patterns
    
    def find_match(self, exception: Exception) -> ErrorPattern:
        """
        Find the best matching pattern for the given exception.
        
        Args:
            exception: The exception to match
            
        Returns:
            Matching ErrorPattern or None if no match found
            
        Note:
            Returns None instead of raising to allow fallback explanation.
        """
        try:
            for pattern in self.patterns:
                if pattern.matches(exception):
                    return pattern
            return None
        except Exception:
            # If pattern matching fails, return None to allow fallback
            return None
    
    def find_all_matches(self, exception: Exception) -> List[ErrorPattern]:
        """
        Find all matching patterns for the given exception.
        
        Args:
            exception: The exception to match
            
        Returns:
            List of matching ErrorPattern objects (may be empty)
        """
        matches = []
        try:
            for pattern in self.patterns:
                if pattern.matches(exception):
                    matches.append(pattern)
        except Exception:
            # If pattern matching fails, return empty list
            pass
        return matches
