"""
Simple menu pattern for interactive console menus.

This module provides the simple_menu() function for creating interactive
console-based menus without complex configuration.

Example:
    def greet():
        print("Hello!")

    def goodbye():
        print("Goodbye!")

    simple_menu({
        "Greet": greet,
        "Say goodbye": goodbye
    })
"""


def simple_menu(options):
    """
    Create an interactive console menu.

    Displays a numbered menu of options and prompts the user to select one.
    The selected option's corresponding function is executed. Invalid selections
    trigger an error message and re-prompt. The menu exits on "quit" or "exit".

    Parameters:
        options (dict): Dictionary where keys are display names (str) and
                       values are callable functions to execute when selected.

    Returns:
        None

    Raises:
        TypeError: If options is not a dictionary or values are not callable.

    Example:
        def save_data():
            print("Data saved!")

        def load_data():
            print("Data loaded!")

        simple_menu({
            "Save": save_data,
            "Load": load_data
        })

    Note:
        - Menu options are displayed with numbers starting from 1
        - User can type "quit" or "exit" to exit the menu
        - Invalid selections display an error and re-prompt
        - Each selected function is called with no arguments
    """
    # Validate input
    if not isinstance(options, dict):
        raise TypeError("options must be a dictionary")
    
    if not options:
        raise ValueError("options dictionary cannot be empty")
    
    # Validate that all values are callable
    for key, value in options.items():
        if not callable(value):
            raise TypeError(f"Value for key '{key}' must be callable")
    
    # Convert options to a list to maintain order and allow indexing
    option_list = list(options.items())
    
    while True:
        # Display menu
        print("\n" + "=" * 40)
        for i, (name, _) in enumerate(option_list, 1):
            print(f"{i}. {name}")
        print("=" * 40)
        
        # Get user input
        user_input = input("Enter your choice (or 'quit'/'exit' to exit): ").strip().lower()
        
        # Check for exit commands
        if user_input in ("quit", "exit"):
            print("Exiting menu.")
            break
        
        # Try to parse as a number
        try:
            choice = int(user_input)
            
            # Check if choice is valid
            if 1 <= choice <= len(option_list):
                # Execute the selected function
                _, func = option_list[choice - 1]
                func()
            else:
                print(f"Error: Please enter a number between 1 and {len(option_list)}.")
        except ValueError:
            print("Error: Invalid input. Please enter a number or 'quit'/'exit'.")
