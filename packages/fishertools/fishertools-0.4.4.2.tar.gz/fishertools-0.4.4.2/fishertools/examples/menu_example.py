"""
Example demonstrating the simple_menu() function from fishertools.patterns.

This example shows how to create an interactive console menu using the
simple_menu() function. The menu allows users to select options and execute
corresponding functions.

Run this file to interact with the menu.
"""

from fishertools.patterns import simple_menu


def show_greeting():
    """Display a greeting message."""
    name = input("What's your name? ")
    print(f"Hello, {name}! Welcome to the menu demo.")


def show_calculator():
    """Simple calculator menu."""
    print("\n--- Simple Calculator ---")
    try:
        a = float(input("Enter first number: "))
        b = float(input("Enter second number: "))
        
        print(f"\nResults:")
        print(f"  {a} + {b} = {a + b}")
        print(f"  {a} - {b} = {a - b}")
        print(f"  {a} * {b} = {a * b}")
        if b != 0:
            print(f"  {a} / {b} = {a / b}")
        else:
            print(f"  {a} / {b} = Cannot divide by zero")
    except ValueError:
        print("❌ Invalid input. Please enter numbers.")


def show_about():
    """Display information about the demo."""
    print("\n--- About This Demo ---")
    print("This is a demonstration of the simple_menu() function")
    print("from fishertools.patterns module.")
    print("\nFeatures:")
    print("  • Interactive menu with numbered options")
    print("  • Easy function execution")
    print("  • Graceful error handling")
    print("  • Exit with 'quit' or 'exit' command")


def list_fruits():
    """Display a list of fruits."""
    fruits = ["Apple", "Banana", "Cherry", "Date", "Elderberry"]
    print("\n--- Available Fruits ---")
    for i, fruit in enumerate(fruits, 1):
        print(f"  {i}. {fruit}")


def show_help():
    """Display help information."""
    print("\n--- Help ---")
    print("This menu demonstrates the simple_menu() function.")
    print("\nHow to use:")
    print("  1. Select an option by entering its number")
    print("  2. Follow the prompts for each option")
    print("  3. Type 'quit' or 'exit' to leave the menu")
    print("\nAvailable options:")
    print("  • Greeting: Get a personalized greeting")
    print("  • Calculator: Perform basic math operations")
    print("  • Fruits: See a list of fruits")
    print("  • About: Learn about this demo")
    print("  • Help: Show this help message")


def main():
    """Run the menu demo."""
    print("=" * 60)
    print("fishertools Patterns - simple_menu() Demo")
    print("=" * 60)
    print("\nWelcome! This demo shows how to use simple_menu().")
    print("Type 'quit' or 'exit' at any time to leave.\n")
    
    # Create the menu with options
    menu_options = {
        "Greeting": show_greeting,
        "Calculator": show_calculator,
        "Fruits": list_fruits,
        "About": show_about,
        "Help": show_help,
    }
    
    # Run the menu
    simple_menu(menu_options)
    
    print("\n" + "=" * 60)
    print("Thank you for using the menu demo!")
    print("=" * 60)


if __name__ == "__main__":
    main()
