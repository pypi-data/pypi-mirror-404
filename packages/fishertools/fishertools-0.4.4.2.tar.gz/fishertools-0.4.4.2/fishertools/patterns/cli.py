"""
SimpleCLI pattern for command-line interface creation.

This module provides the SimpleCLI class for creating command-line interfaces
with minimal boilerplate code. Commands are registered via decorators and
executed based on command-line arguments.

Security features:
- Argument sanitization to prevent injection attacks
- Length limits to prevent DoS attacks
- Input validation

Example:
    cli = SimpleCLI("myapp", "My application")

    @cli.command("greet", "Greet someone")
    def greet(name):
        print(f"Hello, {name}!")

    @cli.command("goodbye", "Say goodbye")
    def goodbye(name):
        print(f"Goodbye, {name}!")

    cli.run()
"""

# Security constants
MAX_ARG_LENGTH = 10000  # Maximum argument length to prevent DoS
MAX_ARGS_COUNT = 100    # Maximum number of arguments


def _sanitize_argument(arg: str, max_length: int = MAX_ARG_LENGTH) -> str:
    """
    Sanitize a command-line argument for security.
    
    Args:
        arg: Argument to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized argument
        
    Raises:
        ValueError: If argument is too long or contains dangerous patterns
    """
    if not isinstance(arg, str):
        raise ValueError(f"Argument must be string, got {type(arg).__name__}")
    
    # Check length to prevent DoS
    if len(arg) > max_length:
        raise ValueError(f"Argument too long (max {max_length} characters)")
    
    # Strip whitespace
    sanitized = arg.strip()
    
    # Check for null bytes (potential injection)
    if '\x00' in sanitized:
        raise ValueError("Null bytes not allowed in arguments")
    
    return sanitized


class SimpleCLI:
    """
    Create command-line interfaces with minimal boilerplate.

    This class provides a decorator-based system for registering commands and
    a run() method for parsing and executing them. Supports --help flag and
    graceful error handling.

    Parameters:
        name (str): The name of the CLI application.
        description (str): A description of what the application does.

    Attributes:
        name (str): The application name.
        description (str): The application description.

    Methods:
        command(name, description): Decorator to register a command.
        run(args=None): Parse and execute commands.

    Raises:
        ValueError: If command registration fails.

    Example:
        cli = SimpleCLI("calculator", "Simple calculator")

        @cli.command("add", "Add two numbers")
        def add(a, b):
            print(f"{a} + {b} = {int(a) + int(b)}")

        @cli.command("multiply", "Multiply two numbers")
        def multiply(a, b):
            print(f"{a} * {b} = {int(a) * int(b)}")

        cli.run()

    Note:
        - Commands are registered via @cli.command() decorator
        - Use --help or -h to show available commands
        - Invalid commands display an error and show help
        - Command handlers receive arguments as strings
        - Each command can have its own parameters
    """

    def __init__(self, name, description):
        """
        Initialize SimpleCLI with name and description.

        Parameters:
            name (str): The name of the CLI application.
            description (str): A description of the application.
        """
        self.name = name
        self.description = description
        self.commands = {}

    def command(self, name, description):
        """
        Decorator to register a command.

        Parameters:
            name (str): The command name.
            description (str): A description of what the command does.

        Returns:
            callable: A decorator function that registers the command.

        Example:
            @cli.command("status", "Show application status")
            def show_status():
                print("Application is running")
        """
        def decorator(func):
            self.commands[name] = {
                "handler": func,
                "description": description
            }
            return func
        return decorator

    def run(self, args=None):
        """
        Parse and execute commands with security checks.

        Parses command-line arguments, sanitizes them, and executes the appropriate
        command handler. Shows help on --help or invalid commands.

        Security features:
        - Argument sanitization
        - Length limits
        - Count limits

        Parameters:
            args (list, optional): Command-line arguments. If None, uses sys.argv[1:].

        Returns:
            None

        Raises:
            ValueError: If arguments fail security checks

        Example:
            cli.run()  # Uses sys.argv
            cli.run(["add", "5", "3"])  # Uses provided args
        """
        import sys
        
        # Use provided args or sys.argv[1:]
        if args is None:
            args = sys.argv[1:]
        
        # Security: Check argument count to prevent DoS
        if len(args) > MAX_ARGS_COUNT:
            print(f"Error: Too many arguments (max {MAX_ARGS_COUNT})")
            return
        
        # Handle no arguments or help flags
        if not args or args[0] in ("--help", "-h"):
            self._show_help()
            return
        
        try:
            # Security: Sanitize all arguments
            sanitized_args = []
            for arg in args:
                try:
                    sanitized = _sanitize_argument(arg)
                    sanitized_args.append(sanitized)
                except ValueError as e:
                    print(f"Error: Invalid argument - {e}")
                    return
            
            # Get the command name
            command_name = sanitized_args[0]
            command_args = sanitized_args[1:]
            
            # Check if command exists
            if command_name not in self.commands:
                print(f"Error: Unknown command '{command_name}'")
                self._show_help()
                return
            
            # Execute the command
            handler = self.commands[command_name]["handler"]
            handler(*command_args)
            
        except TypeError as e:
            print(f"Error: Invalid arguments for command '{command_name}'")
            print(f"Details: {e}")
        except Exception as e:
            print(f"Error: Command '{command_name}' failed")
            print(f"Details: {e}")

    def _show_help(self):
        """
        Display help information.

        Shows the application name, description, and all available commands
        with their descriptions.

        Returns:
            None
        """
        print(f"\n{self.name}")
        print(f"{self.description}")
        print("\nAvailable commands:")
        
        if not self.commands:
            print("  (no commands registered)")
        else:
            for cmd_name, cmd_info in self.commands.items():
                print(f"  {cmd_name:<20} {cmd_info['description']}")
        
        print()
