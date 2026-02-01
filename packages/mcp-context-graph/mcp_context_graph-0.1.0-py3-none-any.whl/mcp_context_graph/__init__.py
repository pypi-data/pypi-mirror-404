"""
MCP-Aware Context Graph: A memory layer for local AI agents.

This package provides a zero-dependency, in-memory graph database
with AST-based dependency tracking and Token-Level Provenance via Source Maps.
"""

import logging
import sys
from typing import Final

__version__: Final[str] = "0.1.0"
__all__ = ["__version__", "logger"]


def _configure_logging() -> logging.Logger:
    """
    Configure all logging to stderr, never stdout.

    Critical Protocol Compliance:
    - NO print() - Breaks JSON-RPC protocol (stdout must be clean)
    - Use logger.debug(), logger.info() only - Direct all output to stderr
    - Never sys.stdout.write() - Corrupts MCP message stream
    """
    _logger = logging.getLogger("mcp_context_graph")
    _logger.setLevel(logging.DEBUG)

    # StreamHandler outputs to stderr by default
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter("[%(levelname)s] %(name)s: %(message)s")
    handler.setFormatter(formatter)
    _logger.addHandler(handler)

    return _logger


# Global logger instance - use this throughout the package
logger = _configure_logging()
