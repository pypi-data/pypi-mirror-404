"""
Patterns module for fishertools.

This module provides reusable pattern templates for common programming tasks,
including menu systems, data storage, logging, and command-line interfaces.

Available patterns:
- simple_menu: Interactive console menu
- JSONStorage: JSON-based data persistence
- SimpleLogger: Simple file-based logging
- SimpleCLI: Command-line interface builder

Example:
    from fishertools.patterns import simple_menu, JSONStorage, SimpleLogger, SimpleCLI

    # Use simple_menu
    def greet():
        print("Hello!")

    simple_menu({"Greet": greet})

    # Use JSONStorage
    storage = JSONStorage("data.json")
    storage.save({"name": "Alice"})
    data = storage.load()

    # Use SimpleLogger
    logger = SimpleLogger("app.log")
    logger.info("Application started")

    # Use SimpleCLI
    cli = SimpleCLI("myapp", "My application")

    @cli.command("greet", "Greet someone")
    def greet_cmd(name):
        print(f"Hello, {name}!")

    cli.run()
"""

from fishertools.patterns.menu import simple_menu
from fishertools.patterns.storage import JSONStorage
from fishertools.patterns.logger import SimpleLogger
from fishertools.patterns.cli import SimpleCLI

__all__ = ["simple_menu", "JSONStorage", "SimpleLogger", "SimpleCLI"]
