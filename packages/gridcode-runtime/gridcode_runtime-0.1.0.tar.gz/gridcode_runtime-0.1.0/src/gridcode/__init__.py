"""GridCode Runtime - Modular Agentic Architecture."""

__version__ = "0.1.0"

from gridcode.core.context import ExecutionContext
from gridcode.core.runtime import GridCodeRuntime

__all__ = ["GridCodeRuntime", "ExecutionContext", "__version__"]
