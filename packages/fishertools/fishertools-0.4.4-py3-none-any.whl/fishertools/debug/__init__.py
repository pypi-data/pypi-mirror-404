"""Debug module for fishertools.

Provides tools for step-by-step debugging and execution tracing.
"""

from .debugger import debug_step_by_step, set_breakpoint
from .tracer import trace

__all__ = ["debug_step_by_step", "set_breakpoint", "trace"]
