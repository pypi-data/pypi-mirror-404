"""
Knowledge Engine Interactive REPL - An interactive command-line interface for exploring Python topics.

This package provides a beginner-friendly REPL for the Knowledge Engine that enables:
- Topic browsing and discovery
- Code execution in a safe sandbox
- Learning progress tracking
- Contextual hints and guidance
"""

def get_repl_engine():
    """Get a REPL engine instance."""
    from fishertools.learn.repl.engine import REPLEngine
    return REPLEngine()


__all__ = [
    "get_repl_engine",
]
