"""
Example demonstrating the SimpleCLI class from fishertools.patterns.

This example shows how to create a command-line interface using SimpleCLI.
Commands are registered via decorators and executed based on command-line
arguments. Supports --help flag and graceful error handling.

Run this file with various commands to see SimpleCLI in action:
  python cli_example.py greet Alice
  python cli_example.py add 5 3
  python cli_example.py --help
"""

from fishertools.patterns import SimpleCLI


def main():
    """Create and run a CLI application."""
    
    # Create a CLI instance
    cli = SimpleCLI("calculator", "A simple calculator application")
    
    # Register commands using decorators
    _register_basic_commands(cli)
    _register_math_commands(cli)
    _register_utility_commands(cli)
    
    # Run the CLI
    cli.run()


def _register_basic_commands(cli):
    """Register basic commands like greet."""
    
    @cli.command("greet", "Greet someone with a message")
    def greet(name="World"):
        """Greet a person by name."""
        print(f"Hello, {name}! Welcome to the calculator app.")


def _register_math_commands(cli):
    """Register mathematical operation commands."""
    
    @cli.command("add", "Add two numbers")
    def add(a, b):
        """Add two numbers and display the result."""
        try:
            result = float(a) + float(b)
            print(f"{a} + {b} = {result}")
        except ValueError:
            print(f"Error: '{a}' and '{b}' must be valid numbers")
    
    @cli.command("subtract", "Subtract two numbers")
    def subtract(a, b):
        """Subtract b from a and display the result."""
        try:
            result = float(a) - float(b)
            print(f"{a} - {b} = {result}")
        except ValueError:
            print(f"Error: '{a}' and '{b}' must be valid numbers")
    
    @cli.command("multiply", "Multiply two numbers")
    def multiply(a, b):
        """Multiply two numbers and display the result."""
        try:
            result = float(a) * float(b)
            print(f"{a} * {b} = {result}")
        except ValueError:
            print(f"Error: '{a}' and '{b}' must be valid numbers")
    
    @cli.command("divide", "Divide two numbers")
    def divide(a, b):
        """Divide a by b and display the result."""
        try:
            a_float = float(a)
            b_float = float(b)
            if b_float == 0:
                print("Error: Cannot divide by zero")
            else:
                result = a_float / b_float
                print(f"{a} / {b} = {result}")
        except ValueError:
            print(f"Error: '{a}' and '{b}' must be valid numbers")
    
    @cli.command("power", "Raise a number to a power")
    def power(base, exponent):
        """Raise base to the power of exponent."""
        try:
            result = float(base) ** float(exponent)
            print(f"{base} ^ {exponent} = {result}")
        except ValueError:
            print(f"Error: '{base}' and '{exponent}' must be valid numbers")
    
    @cli.command("square", "Calculate the square of a number")
    def square(number):
        """Calculate the square of a number."""
        try:
            result = float(number) ** 2
            print(f"{number}² = {result}")
        except ValueError:
            print(f"Error: '{number}' must be a valid number")
    
    @cli.command("sqrt", "Calculate the square root of a number")
    def sqrt(number):
        """Calculate the square root of a number."""
        try:
            num = float(number)
            if num < 0:
                print("Error: Cannot calculate square root of negative number")
            else:
                result = num ** 0.5
                print(f"√{number} = {result}")
        except ValueError:
            print(f"Error: '{number}' must be a valid number")


def _register_utility_commands(cli):
    """Register utility commands like info and demo."""
    
    @cli.command("info", "Show information about this application")
    def show_info():
        """Display information about the calculator."""
        print("\n" + "=" * 60)
        print("Calculator Application - SimpleCLI Demo")
        print("=" * 60)
        print("\nThis is a demonstration of the SimpleCLI pattern from")
        print("fishertools.patterns module.")
        print("\nFeatures:")
        print("  • Command registration via decorators")
        print("  • Automatic help generation")
        print("  • Graceful error handling")
        print("  • Support for multiple arguments")
        print("\nUsage examples:")
        print("  python cli_example.py greet Alice")
        print("  python cli_example.py add 10 5")
        print("  python cli_example.py multiply 3.5 2")
        print("  python cli_example.py divide 20 4")
        print("  python cli_example.py power 2 8")
        print("  python cli_example.py square 7")
        print("  python cli_example.py sqrt 16")
        print("  python cli_example.py --help")
        print("=" * 60 + "\n")
    
    @cli.command("demo", "Run a demonstration of all commands")
    def run_demo():
        """Run a demonstration of all calculator functions."""
        print("\n" + "=" * 60)
        print("Calculator Demo - Running all operations")
        print("=" * 60 + "\n")
        
        print("1. Greeting:")
        greet("Demo User")
        
        print("\n2. Basic arithmetic:")
        add("10", "5")
        subtract("10", "5")
        multiply("10", "5")
        divide("10", "5")
        
        print("\n3. Power operations:")
        power("2", "8")
        square("7")
        sqrt("16")
        
        print("\n" + "=" * 60)
        print("Demo complete!")
        print("=" * 60 + "\n")
    """Create and run a CLI application."""
    
    # Create a CLI instance
    cli = SimpleCLI("calculator", "A simple calculator application")
    
    # Register commands using decorators
    
    @cli.command("greet", "Greet someone with a message")
    def greet(name="World"):
        """Greet a person by name."""
        print(f"Hello, {name}! Welcome to the calculator app.")
    
    @cli.command("add", "Add two numbers")
    def add(a, b):
        """Add two numbers and display the result."""
        try:
            result = float(a) + float(b)
            print(f"{a} + {b} = {result}")
        except ValueError:
            print(f"Error: '{a}' and '{b}' must be valid numbers")
    
    @cli.command("subtract", "Subtract two numbers")
    def subtract(a, b):
        """Subtract b from a and display the result."""
        try:
            result = float(a) - float(b)
            print(f"{a} - {b} = {result}")
        except ValueError:
            print(f"Error: '{a}' and '{b}' must be valid numbers")
    
    @cli.command("multiply", "Multiply two numbers")
    def multiply(a, b):
        """Multiply two numbers and display the result."""
        try:
            result = float(a) * float(b)
            print(f"{a} * {b} = {result}")
        except ValueError:
            print(f"Error: '{a}' and '{b}' must be valid numbers")
    
    @cli.command("divide", "Divide two numbers")
    def divide(a, b):
        """Divide a by b and display the result."""
        try:
            a_float = float(a)
            b_float = float(b)
            if b_float == 0:
                print("Error: Cannot divide by zero")
            else:
                result = a_float / b_float
                print(f"{a} / {b} = {result}")
        except ValueError:
            print(f"Error: '{a}' and '{b}' must be valid numbers")
    
    @cli.command("power", "Raise a number to a power")
    def power(base, exponent):
        """Raise base to the power of exponent."""
        try:
            result = float(base) ** float(exponent)
            print(f"{base} ^ {exponent} = {result}")
        except ValueError:
            print(f"Error: '{base}' and '{exponent}' must be valid numbers")
    
    @cli.command("square", "Calculate the square of a number")
    def square(number):
        """Calculate the square of a number."""
        try:
            result = float(number) ** 2
            print(f"{number}² = {result}")
        except ValueError:
            print(f"Error: '{number}' must be a valid number")
    
    @cli.command("sqrt", "Calculate the square root of a number")
    def sqrt(number):
        """Calculate the square root of a number."""
        try:
            num = float(number)
            if num < 0:
                print("Error: Cannot calculate square root of negative number")
            else:
                result = num ** 0.5
                print(f"√{number} = {result}")
        except ValueError:
            print(f"Error: '{number}' must be a valid number")
    
    @cli.command("info", "Show information about this application")
    def show_info():
        """Display information about the calculator."""
        print("\n" + "=" * 60)
        print("Calculator Application - SimpleCLI Demo")
        print("=" * 60)
        print("\nThis is a demonstration of the SimpleCLI pattern from")
        print("fishertools.patterns module.")
        print("\nFeatures:")
        print("  • Command registration via decorators")
        print("  • Automatic help generation")
        print("  • Graceful error handling")
        print("  • Support for multiple arguments")
        print("\nUsage examples:")
        print("  python cli_example.py greet Alice")
        print("  python cli_example.py add 10 5")
        print("  python cli_example.py multiply 3.5 2")
        print("  python cli_example.py divide 20 4")
        print("  python cli_example.py power 2 8")
        print("  python cli_example.py square 7")
        print("  python cli_example.py sqrt 16")
        print("  python cli_example.py --help")
        print("=" * 60 + "\n")
    
    @cli.command("demo", "Run a demonstration of all commands")
    def run_demo():
        """Run a demonstration of all calculator functions."""
        print("\n" + "=" * 60)
        print("Calculator Demo - Running all operations")
        print("=" * 60 + "\n")
        
        print("1. Greeting:")
        greet("Demo User")
        
        print("\n2. Basic arithmetic:")
        add("10", "5")
        subtract("10", "5")
        multiply("10", "5")
        divide("10", "5")
        
        print("\n3. Power operations:")
        power("2", "8")
        square("7")
        sqrt("16")
        
        print("\n" + "=" * 60)
        print("Demo complete!")
        print("=" * 60 + "\n")
    
    # Run the CLI
    cli.run()


if __name__ == "__main__":
    main()
