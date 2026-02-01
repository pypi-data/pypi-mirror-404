"""
Main REPL Engine for the Knowledge Engine Interactive REPL.

This module provides the main loop and orchestration for the REPL system.
"""

from typing import Optional, List, Tuple
from fishertools.learn.knowledge_engine import KnowledgeEngine
from fishertools.learn.repl.command_parser import CommandParser
from fishertools.learn.repl.command_handler import CommandHandler
from fishertools.learn.repl.code_sandbox import CodeSandbox
from fishertools.learn.repl.session_manager import SessionManager


class REPLEngine:
    """
    Main REPL engine that orchestrates user interaction.
    
    Manages:
    - User input parsing
    - Command execution
    - Topic display
    - Session state
    - Code execution
    
    Example:
        >>> engine = REPLEngine()
        >>> engine.start()
    """
    
    WELCOME_MESSAGE = """
╔════════════════════════════════════════════════════════════════╗
║     Welcome to the Knowledge Engine Interactive REPL! 🎓      ║
║                                                                ║
║  Learn Python concepts interactively with examples and tips.  ║
║  Type /help to see available commands.                        ║
║  Type /exit or /quit to exit.                                 ║
╚════════════════════════════════════════════════════════════════╝
"""
    
    def __init__(self, engine: Optional[KnowledgeEngine] = None, 
                 session_manager: Optional[SessionManager] = None):
        """
        Initialize the REPL engine.
        
        Args:
            engine: Optional Knowledge Engine instance (creates new if not provided)
            session_manager: Optional SessionManager instance (creates new if not provided)
        """
        self.engine = engine or KnowledgeEngine()
        self.session_manager = session_manager or SessionManager()
        self.command_handler = CommandHandler(self.engine, self.session_manager)
        self.code_sandbox = CodeSandbox()
        self.parser = CommandParser()
        
        self.current_topic: Optional[str] = None
        self.in_edit_mode = False
        self.edit_topic: Optional[str] = None
        self.edit_example_num: Optional[int] = None
        self.edit_code: str = ""
        self.running = False
    
    def start(self) -> None:
        """
        Start the interactive REPL loop.
        
        Displays welcome message and enters main loop.
        """
        print(self.WELCOME_MESSAGE)
        
        # Load previous session if available
        if self.session_manager.get_current_topic():
            self.current_topic = self.session_manager.get_current_topic()
            print(f"📚 Resuming previous session. Last topic: {self.current_topic}\n")
        
        self.running = True
        
        try:
            while self.running:
                self._prompt_and_process()
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye! Your progress has been saved.")
            self.session_manager.save_session()
        except Exception as e:
            print(f"\n❌ An unexpected error occurred: {e}")
            print("Your progress has been saved.")
            self.session_manager.save_session()
    
    def _prompt_and_process(self) -> None:
        """
        Prompt for user input and process it.
        """
        try:
            if self.in_edit_mode:
                prompt = f"[Edit {self.edit_topic} Example {self.edit_example_num}]> "
            elif self.current_topic:
                prompt = f"[{self.current_topic}]> "
            else:
                prompt = "> "
            
            user_input = input(prompt).strip()
            
            if not user_input:
                return
            
            self._process_input(user_input)
        
        except EOFError:
            self.running = False
    
    def _process_input(self, user_input: str) -> None:
        """
        Process user input.
        
        Args:
            user_input: The user's input string
        """
        try:
            cmd_type, args = self.parser.parse(user_input)
        except ValueError as e:
            print(f"❌ {e}")
            return
        
        if cmd_type == "command":
            self._handle_command(args)
        elif cmd_type == "topic":
            self._handle_topic_input(args[0])
    
    def _handle_command(self, args: List[str]) -> None:
        """
        Handle a command.
        
        Args:
            args: Command and arguments [command_name, arg1, arg2, ...]
        """
        command = args[0]
        command_args = args[1:] if len(args) > 1 else []
        
        # Exit commands
        if self._handle_exit_commands(command):
            return
        
        # Edit mode commands
        if self.in_edit_mode:
            self._handle_edit_mode_commands(command)
            return
        
        # Route to appropriate handler
        if self._handle_topic_browsing_commands(command, command_args):
            return
        elif self._handle_navigation_commands(command, command_args):
            return
        elif self._handle_code_execution_commands(command, command_args):
            return
        elif self._handle_progress_commands(command, command_args):
            return
        elif self._handle_session_commands(command, command_args):
            return
        elif self._handle_help_commands(command, command_args):
            return
        else:
            print(f"❌ Unknown command: {command}")
    
    def _handle_exit_commands(self, command: str) -> bool:
        """Handle exit commands."""
        if command in ["exit", "quit"]:
            print("👋 Goodbye! Your progress has been saved.")
            self.session_manager.save_session()
            self.running = False
            return True
        return False
    
    def _handle_edit_mode_commands(self, command: str) -> None:
        """Handle commands while in edit mode."""
        if command == "exit_edit":
            self._exit_edit_mode()
        else:
            print("❌ You are in edit mode. Type /exit_edit to exit.")
    
    def _handle_topic_browsing_commands(self, command: str, command_args: List[str]) -> bool:
        """Handle topic browsing commands."""
        if command == "list":
            output = self.command_handler.handle_list()
            print(output)
            return True
        elif command == "search":
            keyword = " ".join(command_args) if command_args else ""
            output = self.command_handler.handle_search(keyword)
            print(output)
            return True
        elif command == "random":
            output = self.command_handler.handle_random()
            print(output)
            return True
        elif command == "categories":
            output = self.command_handler.handle_categories()
            print(output)
            return True
        elif command == "category":
            category = " ".join(command_args) if command_args else ""
            output = self.command_handler.handle_category(category)
            print(output)
            return True
        elif command == "path":
            output = self.command_handler.handle_path()
            print(output)
            return True
        elif command == "related":
            output = self.command_handler.handle_related(self.current_topic)
            print(output)
            return True
        return False
    
    def _handle_navigation_commands(self, command: str, command_args: List[str]) -> bool:
        """Handle navigation commands."""
        if command == "next":
            self._navigate_next()
            return True
        elif command == "prev":
            self._navigate_prev()
            return True
        elif command == "goto":
            topic = " ".join(command_args) if command_args else ""
            self._navigate_to_topic(topic)
            return True
        return False
    
    def _handle_code_execution_commands(self, command: str, command_args: List[str]) -> bool:
        """Handle code execution commands."""
        if command == "run":
            return self._handle_run_command(command_args)
        elif command == "modify":
            return self._handle_modify_command(command_args)
        return False
    
    def _handle_run_command(self, command_args: List[str]) -> bool:
        """Handle the run command."""
        if not self.current_topic:
            print("❌ No current topic. View a topic first.")
            return False
        
        if not command_args:
            print("❌ Please provide an example number.\nUsage: /run <number>")
            return False
        
        try:
            example_num = int(command_args[0])
            self._run_example(example_num)
            return True
        except ValueError:
            print("❌ Example number must be an integer.")
            return False
    
    def _handle_modify_command(self, command_args: List[str]) -> bool:
        """Handle the modify command."""
        if not self.current_topic:
            print("❌ No current topic. View a topic first.")
            return False
        
        if not command_args:
            print("❌ Please provide an example number.\nUsage: /modify <number>")
            return False
        
        try:
            example_num = int(command_args[0])
            self._enter_edit_mode(example_num)
            return True
        except ValueError:
            print("❌ Example number must be an integer.")
            return False
        """Handle the modify command."""
        if not self.current_topic:
            print("❌ No current topic. View a topic first.")
            return True
        
        if not command_args:
            print("❌ Please provide an example number.\nUsage: /modify <number>")
            return True
        
        try:
            example_num = int(command_args[0])
            self._enter_edit_mode(example_num)
        except ValueError:
            print("❌ Example number must be an integer.")
        return True
    
    def _handle_progress_commands(self, command: str, command_args: List[str]) -> bool:
        """Handle progress tracking commands."""
        if command == "progress":
            output = self.command_handler.handle_progress()
            print(output)
            return True
        elif command == "stats":
            output = self.command_handler.handle_stats()
            print(output)
            return True
        elif command == "reset_progress":
            self._handle_reset_progress()
            return True
        return False
    
    def _handle_reset_progress(self) -> None:
        """Handle progress reset with confirmation."""
        response = input("⚠️  Are you sure you want to reset all progress? (yes/no): ").strip().lower()
        if response == "yes":
            self.session_manager.reset_progress()
            print("✅ Progress reset.")
        else:
            print("❌ Reset cancelled.")
    
    def _handle_session_commands(self, command: str, command_args: List[str]) -> bool:
        """Handle session management commands."""
        if command == "history":
            self._handle_history_command()
            return True
        elif command == "clear_history":
            self._handle_clear_history()
            return True
        elif command == "session":
            self._handle_session_info()
            return True
        return False
    
    def _handle_history_command(self) -> None:
        """Handle the history command."""
        history = self.session_manager.get_session_history()
        if not history:
            print("📋 Session history is empty.")
        else:
            print("📋 Session History:")
            for i, topic in enumerate(history, 1):
                print(f"  {i}. {topic}")
    
    def _handle_clear_history(self) -> None:
        """Handle clear history with confirmation."""
        response = input("⚠️  Are you sure you want to clear session history? (yes/no): ").strip().lower()
        if response == "yes":
            self.session_manager.clear_session_history()
            print("✅ History cleared.")
        else:
            print("❌ Clear cancelled.")
    
    def _handle_session_info(self) -> None:
        """Handle session info display."""
        info = self.session_manager.get_session_info()
        print("📊 Session Information:")
        for key, value in info.items():
            print(f"  {key}: {value}")
    
    def _handle_help_commands(self, command: str, command_args: List[str]) -> bool:
        """Handle help and information commands."""
        if command == "help":
            help_cmd = command_args[0] if command_args else None
            output = self.command_handler.handle_help(help_cmd)
            print(output)
            return True
        elif command == "commands":
            output = self.command_handler.handle_commands()
            print(output)
            return True
        elif command == "about":
            output = self.command_handler.handle_about()
            print(output)
            return True
        elif command == "hint":
            output = self.command_handler.handle_hint(self.current_topic)
            print(output)
            return True
        elif command == "tip":
            output = self.command_handler.handle_tip()
            print(output)
            return True
        elif command == "tips":
            output = self.command_handler.handle_tips(self.current_topic)
            print(output)
            return True
        return False
    
    def _handle_topic_input(self, topic_name: str) -> None:
        """
        Handle topic name input.
        
        Args:
            topic_name: Name of the topic to display
        """
        topic = self.engine.get_topic(topic_name)
        
        if not topic:
            # Try fuzzy matching
            from difflib import get_close_matches
            all_topics = self.engine.list_topics()
            suggestions = get_close_matches(topic_name, all_topics, n=3, cutoff=0.6)
            
            print(f"❌ Topic '{topic_name}' not found.")
            if suggestions:
                print("\nDid you mean:")
                for suggestion in suggestions:
                    print(f"  • {suggestion}")
            return
        
        self._display_topic(topic_name)
    
    def _display_topic(self, topic_name: str) -> None:
        """
        Display a topic.
        
        Args:
            topic_name: Name of the topic to display
        """
        self.current_topic = topic_name
        self.session_manager.set_current_topic(topic_name)
        self.session_manager.mark_topic_viewed(topic_name)
        
        output = self.command_handler.format_topic_display(topic_name)
        print(output)
    
    def _run_example(self, example_num: int) -> None:
        """
        Run a code example.
        
        Args:
            example_num: Number of the example to run
        """
        topic = self.engine.get_topic(self.current_topic)
        if not topic:
            print("❌ Topic not found.")
            return
        
        examples = topic.get("examples", [])
        
        # Find the example (examples are 1-indexed)
        if example_num < 1 or example_num > len(examples):
            print(f"❌ Invalid example number. Available examples: 1-{len(examples)}")
            return
        
        example = examples[example_num - 1]
        code = example.get("code", "")
        
        if not code:
            print("❌ Example has no code.")
            return
        
        print(f"\n▶️  Running Example {example_num}...\n")
        
        success, output = self.code_sandbox.execute(code)
        
        if success:
            print(f"✅ Output:\n{output}")
            self.session_manager.mark_example_executed(self.current_topic, example_num)
        else:
            print(f"❌ Error:\n{output}")
    
    def _enter_edit_mode(self, example_num: int) -> None:
        """
        Enter edit mode for an example.
        
        Args:
            example_num: Number of the example to edit
        """
        topic = self.engine.get_topic(self.current_topic)
        if not topic:
            print("❌ Topic not found.")
            return
        
        examples = topic.get("examples", [])
        
        if example_num < 1 or example_num > len(examples):
            print(f"❌ Invalid example number. Available examples: 1-{len(examples)}")
            return
        
        example = examples[example_num - 1]
        code = example.get("code", "")
        
        if not code:
            print("❌ Example has no code.")
            return
        
        self.in_edit_mode = True
        self.edit_topic = self.current_topic
        self.edit_example_num = example_num
        self.edit_code = code
        
        print(f"\n✏️  Editing Example {example_num}:")
        print("=" * 50)
        print(self.edit_code)
        print("=" * 50)
        print("Enter new code (type /exit_edit when done):")
    
    def _exit_edit_mode(self) -> None:
        """
        Exit edit mode and execute the modified code.
        """
        if not self.in_edit_mode:
            print("❌ Not in edit mode.")
            return
        
        print(f"\n▶️  Running modified Example {self.edit_example_num}...\n")
        
        success, output = self.code_sandbox.execute(self.edit_code)
        
        if success:
            print(f"✅ Output:\n{output}")
            self.session_manager.mark_example_executed(self.current_topic, self.edit_example_num)
        else:
            print(f"❌ Error:\n{output}")
        
        self.in_edit_mode = False
        self.edit_topic = None
        self.edit_example_num = None
        self.edit_code = ""
    
    def _navigate_next(self) -> None:
        """Navigate to the next topic in the learning path."""
        path = self.engine.get_learning_path()
        
        if not self.current_topic:
            if path:
                self._display_topic(path[0])
            else:
                print("❌ No topics available.")
            return
        
        try:
            current_index = path.index(self.current_topic)
            if current_index < len(path) - 1:
                next_topic = path[current_index + 1]
                self._display_topic(next_topic)
            else:
                print("📍 You are at the last topic in the learning path.")
        except ValueError:
            print("❌ Current topic not in learning path.")
    
    def _navigate_prev(self) -> None:
        """Navigate to the previous topic in the learning path."""
        path = self.engine.get_learning_path()
        
        if not self.current_topic:
            print("❌ No current topic.")
            return
        
        try:
            current_index = path.index(self.current_topic)
            if current_index > 0:
                prev_topic = path[current_index - 1]
                self._display_topic(prev_topic)
            else:
                print("📍 You are at the first topic in the learning path.")
        except ValueError:
            print("❌ Current topic not in learning path.")
    
    def _navigate_to_topic(self, topic_name: str) -> None:
        """
        Navigate to a specific topic.
        
        Args:
            topic_name: Name of the topic to navigate to
        """
        if not topic_name:
            print("❌ Please provide a topic name.\nUsage: /goto <topic_name>")
            return
        
        self._handle_topic_input(topic_name)
