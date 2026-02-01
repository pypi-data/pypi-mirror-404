"""
Command handler for the Knowledge Engine REPL.

This module handles execution of all REPL commands and returns formatted output.
"""

import random
from typing import List, Dict, Optional, Any
from difflib import get_close_matches

from fishertools.learn.knowledge_engine import KnowledgeEngine
from fishertools.learn.repl.session_manager import SessionManager
from fishertools.learn.repl.models import TopicDisplay, ExampleDisplay


class CommandHandler:
    """
    Handles execution of REPL commands and returns formatted output.
    
    Supports commands for:
    - Topic browsing (/list, /search, /random, /categories, /category, /path)
    - Topic information (/related)
    - Progress tracking (/progress, /stats)
    - Help and information (/help, /commands, /about)
    - Hints and tips (/hint, /tip, /tips)
    
    Example:
        >>> engine = KnowledgeEngine()
        >>> manager = SessionManager()
        >>> handler = CommandHandler(engine, manager)
        >>> output = handler.handle_list()
        >>> print(output)
    """
    
    # Message constants
    TYPE_TOPIC_MESSAGE = "Type a topic name to view it.\n"
    NO_CURRENT_TOPIC_MESSAGE = "❌ No current topic. View a topic first.\n"
    
    def __init__(self, engine: KnowledgeEngine, session_manager: SessionManager):
        """
        Initialize the command handler.
        
        Args:
            engine: Knowledge Engine instance
            session_manager: Session Manager instance
        """
        self.engine = engine
        self.session_manager = session_manager
    
    def handle_list(self) -> str:
        """
        Handle /list command - display all topics organized by category.
        
        Returns:
            Formatted string with all topics organized by category
        """
        output = "📚 Available Topics:\n"
        output += "=" * 50 + "\n\n"
        
        categories = sorted(self.engine.categories.keys())
        
        for category in categories:
            topics = self.engine.get_topics_by_category(category)
            output += f"📂 {category}\n"
            for topic in topics:
                output += f"   • {topic}\n"
            output += "\n"
        
        output += f"Total topics: {len(self.engine.list_topics())}\n"
        output += "Type a topic name to view it, or use /search <keyword> to find topics.\n"
        
        return output
    
    def handle_search(self, keyword: str) -> str:
        """
        Handle /search command - search for topics by keyword.
        
        Args:
            keyword: Keyword to search for
        
        Returns:
            Formatted string with search results
        """
        if not keyword or not keyword.strip():
            return "❌ Please provide a search keyword.\nUsage: /search <keyword>"
        
        results = self.engine.search_topics(keyword)
        
        if not results:
            # Try fuzzy matching for suggestions
            all_topics = self.engine.list_topics()
            suggestions = get_close_matches(keyword, all_topics, n=3, cutoff=0.6)
            
            output = f"❌ No topics found for '{keyword}'.\n"
            if suggestions:
                output += "\nDid you mean:\n"
                for suggestion in suggestions:
                    output += f"   • {suggestion}\n"
            return output
        
        output = f"🔍 Search results for '{keyword}':\n"
        output += "=" * 50 + "\n\n"
        
        for topic in results:
            output += f"• {topic}\n"
        
        output += f"\nFound {len(results)} topic(s).\n"
        output += self.TYPE_TOPIC_MESSAGE
        
        return output
    
    def handle_random(self) -> str:
        """
        Handle /random command - display a random topic.
        
        Returns:
            Formatted string with random topic name
        """
        topic_dict = self.engine.get_random_topic()
        topic_name = topic_dict.get("topic", "Unknown")
        
        output = f"🎲 Random topic: {topic_name}\n"
        output += f"Type '{topic_name}' to view it.\n"
        
        return output
    
    def handle_categories(self) -> str:
        """
        Handle /categories command - display all available categories.
        
        Returns:
            Formatted string with all categories
        """
        output = "📂 Available Categories:\n"
        output += "=" * 50 + "\n\n"
        
        categories = sorted(self.engine.categories.keys())
        
        for category in categories:
            count = len(self.engine.get_topics_by_category(category))
            output += f"• {category} ({count} topics)\n"
        
        output += f"\nTotal categories: {len(categories)}\n"
        output += "Use /category <name> to view topics in a category.\n"
        
        return output
    
    def handle_category(self, category_name: str) -> str:
        """
        Handle /category command - display topics in a category.
        
        Args:
            category_name: Name of the category
        
        Returns:
            Formatted string with topics in the category
        """
        if not category_name or not category_name.strip():
            return "❌ Please provide a category name.\nUsage: /category <name>"
        
        topics = self.engine.get_topics_by_category(category_name)
        
        if not topics:
            # Try fuzzy matching
            all_categories = list(self.engine.categories.keys())
            suggestions = get_close_matches(category_name, all_categories, n=3, cutoff=0.6)
            
            output = f"❌ Category '{category_name}' not found.\n"
            if suggestions:
                output += "\nDid you mean:\n"
                for suggestion in suggestions:
                    output += f"   • {suggestion}\n"
            return output
        
        output = f"📂 Topics in '{category_name}':\n"
        output += "=" * 50 + "\n\n"
        
        for topic in topics:
            output += f"• {topic}\n"
        
        output += f"\nTotal topics: {len(topics)}\n"
        output += self.TYPE_TOPIC_MESSAGE
        
        return output
    
    def handle_path(self) -> str:
        """
        Handle /path command - display the recommended learning path.
        
        Returns:
            Formatted string with learning path
        """
        path = self.engine.get_learning_path()
        
        output = "🛤️  Recommended Learning Path:\n"
        output += "=" * 50 + "\n\n"
        
        for i, topic_name in enumerate(path, 1):
            topic = self.engine.get_topic(topic_name)
            difficulty = topic.get("difficulty", "Unknown")
            output += f"{i}. {topic_name} ({difficulty})\n"
        
        output += f"\nTotal topics: {len(path)}\n"
        output += "Type a topic name to start learning.\n"
        
        return output
    
    def handle_related(self, topic_name: str) -> str:
        """
        Handle /related command - display related topics.
        
        Args:
            topic_name: Name of the current topic
        
        Returns:
            Formatted string with related topics
        """
        if not topic_name:
            return self.NO_CURRENT_TOPIC_MESSAGE
        
        related = self.engine.get_related_topics(topic_name)
        
        if not related:
            return f"ℹ️  No related topics for '{topic_name}'.\n"
        
        output = f"🔗 Topics related to '{topic_name}':\n"
        output += "=" * 50 + "\n\n"
        
        for topic in related:
            output += f"• {topic}\n"
        
        output += f"\nTotal related topics: {len(related)}\n"
        output += self.TYPE_TOPIC_MESSAGE
        
        return output
    
    def handle_progress(self) -> str:
        """
        Handle /progress command - display learning progress.
        
        Returns:
            Formatted string with progress statistics
        """
        progress = self.session_manager.get_progress()
        
        output = "📊 Learning Progress:\n"
        output += "=" * 50 + "\n\n"
        output += f"Topics viewed: {progress.viewed_topics}\n"
        output += f"Examples executed: {progress.executed_examples}\n"
        output += f"Session duration: {progress.session_duration:.1f} seconds\n"
        
        if progress.last_viewed_topic:
            output += f"Last viewed topic: {progress.last_viewed_topic}\n"
        
        return output
    
    def handle_stats(self) -> str:
        """
        Handle /stats command - display detailed statistics.
        
        Returns:
            Formatted string with detailed statistics
        """
        progress = self.session_manager.get_progress()
        session_info = self.session_manager.get_session_info()
        
        output = "📈 Detailed Statistics:\n"
        output += "=" * 50 + "\n\n"
        output += f"Topics viewed: {progress.viewed_topics}\n"
        output += f"Examples executed: {progress.executed_examples}\n"
        output += f"Session duration: {session_info['session_duration_seconds']:.1f} seconds\n"
        output += f"Session history length: {session_info['session_history_length']}\n"
        output += f"Created at: {session_info['created_at']}\n"
        output += f"Last updated: {session_info['last_updated']}\n"
        
        return output
    
    def handle_hint(self, topic_name: str) -> str:
        """
        Handle /hint command - display a hint for the current topic.
        
        Args:
            topic_name: Name of the current topic
        
        Returns:
            Formatted string with a hint
        """
        if not topic_name:
            return self.NO_CURRENT_TOPIC_MESSAGE
        
        topic = self.engine.get_topic(topic_name)
        if not topic:
            return f"❌ Topic '{topic_name}' not found.\n"
        
        tips = topic.get("tips", [])
        if not tips:
            return f"ℹ️  No hints available for '{topic_name}'.\n"
        
        hint = random.choice(tips)
        
        output = f"💡 Hint for '{topic_name}':\n"
        output += "=" * 50 + "\n\n"
        output += f"{hint}\n"
        
        return output
    
    def handle_tip(self) -> str:
        """
        Handle /tip command - display a learning tip.
        
        Returns:
            Formatted string with a learning tip
        """
        tips = [
            "💡 Try modifying the examples to see how they work!",
            "💡 Use /search to find topics related to what you're learning.",
            "💡 Check /progress to see how much you've learned.",
            "💡 Use /related to explore connected concepts.",
            "💡 Practice by running and modifying examples.",
            "💡 Read the common mistakes section to avoid errors.",
            "💡 Use /path to follow a structured learning path.",
        ]
        
        tip = random.choice(tips)
        return f"{tip}\n"
    
    def handle_tips(self, topic_name: str) -> str:
        """
        Handle /tips command - display all tips for a topic.
        
        Args:
            topic_name: Name of the current topic
        
        Returns:
            Formatted string with all tips
        """
        if not topic_name:
            return self.NO_CURRENT_TOPIC_MESSAGE
        
        topic = self.engine.get_topic(topic_name)
        if not topic:
            return f"❌ Topic '{topic_name}' not found.\n"
        
        tips = topic.get("tips", [])
        if not tips:
            return f"ℹ️  No tips available for '{topic_name}'.\n"
        
        output = f"💡 Tips for '{topic_name}':\n"
        output += "=" * 50 + "\n\n"
        
        for i, tip in enumerate(tips, 1):
            output += f"{i}. {tip}\n"
        
        return output
    
    def handle_help(self, command: Optional[str] = None) -> str:
        """
        Handle /help command - display help information.
        
        Args:
            command: Optional specific command to get help for
        
        Returns:
            Formatted string with help information
        """
        if command:
            return self._get_command_help(command)
        
        output = "📖 Available Commands:\n"
        output += "=" * 50 + "\n\n"
        output += "Topic Browsing:\n"
        output += "  /list              - Show all topics by category\n"
        output += "  /search <keyword>  - Search for topics\n"
        output += "  /random            - Show a random topic\n"
        output += "  /categories        - Show all categories\n"
        output += "  /category <name>   - Show topics in a category\n"
        output += "  /path              - Show recommended learning path\n\n"
        output += "Topic Navigation:\n"
        output += "  /related           - Show related topics\n"
        output += "  /next              - Go to next topic in path\n"
        output += "  /prev              - Go to previous topic in path\n"
        output += "  /goto <topic>      - Go to specific topic\n\n"
        output += "Code Execution:\n"
        output += "  /run <num>         - Run example number\n"
        output += "  /modify <num>      - Modify and run example\n"
        output += "  /exit_edit         - Exit edit mode\n\n"
        output += "Progress Tracking:\n"
        output += "  /progress          - Show learning progress\n"
        output += "  /stats             - Show detailed statistics\n"
        output += "  /reset_progress    - Reset all progress\n\n"
        output += "Session Management:\n"
        output += "  /history           - Show session history\n"
        output += "  /clear_history     - Clear session history\n"
        output += "  /session           - Show session info\n\n"
        output += "Help and Information:\n"
        output += "  /help              - Show this help message\n"
        output += "  /help <command>    - Get help for a command\n"
        output += "  /commands          - Show all commands\n"
        output += "  /about             - About the REPL\n"
        output += "  /hint              - Get a hint for current topic\n"
        output += "  /tip               - Get a learning tip\n"
        output += "  /tips              - Show all tips for current topic\n\n"
        output += "Session Control:\n"
        output += "  /exit, /quit       - Exit the REPL\n\n"
        output += "Type /help <command> for more details on a specific command.\n"
        
        return output
    
    def _get_command_help(self, command: str) -> str:
        """
        Get detailed help for a specific command.
        
        Args:
            command: Command name
        
        Returns:
            Formatted help text for the command
        """
        help_text = {
            "list": "Show all available topics organized by category.\nUsage: /list",
            "search": "Search for topics by keyword.\nUsage: /search <keyword>\nExample: /search list",
            "random": "Display a random topic to encourage exploration.\nUsage: /random",
            "categories": "Show all available topic categories.\nUsage: /categories",
            "category": "Show all topics in a specific category.\nUsage: /category <name>\nExample: /category \"Basic Types\"",
            "path": "Show the recommended learning path from beginner to advanced.\nUsage: /path",
            "related": "Show topics related to the current topic.\nUsage: /related",
            "progress": "Show your learning progress.\nUsage: /progress",
            "stats": "Show detailed learning statistics.\nUsage: /stats",
            "hint": "Get a hint for the current topic.\nUsage: /hint",
            "tip": "Get a random learning tip.\nUsage: /tip",
            "tips": "Show all tips for the current topic.\nUsage: /tips",
            "help": "Show help information.\nUsage: /help or /help <command>",
            "run": "Run a code example.\nUsage: /run <example_number>\nExample: /run 1",
            "modify": "Modify and run a code example.\nUsage: /modify <example_number>\nExample: /modify 1",
            "exit_edit": "Exit edit mode.\nUsage: /exit_edit",
            "history": "Show your session history.\nUsage: /history",
            "clear_history": "Clear your session history.\nUsage: /clear_history",
            "session": "Show current session information.\nUsage: /session",
            "reset_progress": "Reset all learning progress.\nUsage: /reset_progress",
            "commands": "Show all available commands.\nUsage: /commands",
            "about": "Show information about the REPL.\nUsage: /about",
            "exit": "Exit the REPL.\nUsage: /exit or /quit",
            "quit": "Exit the REPL.\nUsage: /quit or /exit",
        }
        
        command_lower = command.lower()
        if command_lower in help_text:
            return f"📖 Help for '{command}':\n" + "=" * 50 + "\n\n" + help_text[command_lower] + "\n"
        else:
            return f"❌ No help available for '{command}'.\nType /help to see all commands.\n"
    
    def handle_commands(self) -> str:
        """
        Handle /commands command - show all commands categorized.
        
        Returns:
            Formatted string with all commands
        """
        output = "📋 All Commands:\n"
        output += "=" * 50 + "\n\n"
        output += "Topic Browsing: /list, /search, /random, /categories, /category, /path\n"
        output += "Navigation: /related, /next, /prev, /goto\n"
        output += "Code: /run, /modify, /exit_edit\n"
        output += "Progress: /progress, /stats, /reset_progress\n"
        output += "Session: /history, /clear_history, /session\n"
        output += "Help: /help, /commands, /about, /hint, /tip, /tips\n"
        output += "Control: /exit, /quit\n\n"
        output += "Type /help <command> for details on a specific command.\n"
        
        return output
    
    def handle_about(self) -> str:
        """
        Handle /about command - show information about the REPL.
        
        Returns:
            Formatted string with about information
        """
        output = "ℹ️  About Knowledge Engine REPL:\n"
        output += "=" * 50 + "\n\n"
        output += "The Knowledge Engine REPL is an interactive learning tool for Python.\n"
        output += "It provides:\n"
        output += "  • Interactive topic browsing and discovery\n"
        output += "  • Safe code execution in a sandbox environment\n"
        output += "  • Learning progress tracking\n"
        output += "  • Contextual hints and guidance\n"
        output += "  • Session persistence for resuming learning\n\n"
        output += "Type /help to get started.\n"
        
        return output
    
    def format_topic_display(self, topic_name: str) -> str:
        """
        Format a topic for display.
        
        Args:
            topic_name: Name of the topic to display
        
        Returns:
            Formatted string with topic information
        """
        topic = self.engine.get_topic(topic_name)
        if not topic:
            return f"❌ Topic '{topic_name}' not found.\n"
        
        output = f"\n📚 {topic_name}\n"
        output += "=" * 50 + "\n\n"
        
        # Category and difficulty
        category = topic.get("category", "Unknown")
        difficulty = topic.get("difficulty", "Unknown")
        output += f"Category: {category} | Difficulty: {difficulty}\n\n"
        
        # Description
        description = topic.get("description", "")
        if description:
            output += f"Description:\n{description}\n\n"
        
        # Examples
        examples = topic.get("examples", [])
        if examples:
            output += "Examples:\n"
            for i, example in enumerate(examples, 1):
                output += f"\n  Example {i}: {example.get('description', '')}\n"
                output += f"  ```python\n"
                code_lines = example.get('code', '').split('\n')
                for line in code_lines:
                    output += f"  {line}\n"
                output += f"  ```\n"
        
        # Common mistakes
        mistakes = topic.get("common_mistakes", [])
        if mistakes:
            output += "\nCommon Mistakes:\n"
            for mistake in mistakes:
                output += f"  ⚠️  {mistake}\n"
        
        # Related topics
        related = self.engine.get_related_topics(topic_name)
        if related:
            output += "\nRelated Topics:\n"
            for related_topic in related:
                output += f"  • {related_topic}\n"
        
        output += "\n" + "=" * 50 + "\n"
        output += "Commands: /run <num>, /modify <num>, /related, /next, /prev, /goto <topic>\n"
        
        return output
