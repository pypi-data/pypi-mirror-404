"""
Command-line interface entry point for the Knowledge Engine REPL.

This module provides the main entry point for running the REPL from the command line.
"""

import sys
from fishertools.learn.repl.engine import REPLEngine


def main() -> int:
    """
    Main entry point for the REPL.
    
    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        engine = REPLEngine()
        engine.start()
        return 0
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        return 0
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
