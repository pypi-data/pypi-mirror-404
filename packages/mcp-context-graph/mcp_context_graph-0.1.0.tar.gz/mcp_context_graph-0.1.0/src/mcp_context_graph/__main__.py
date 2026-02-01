"""
Allow running the package as a module.

Usage:
    python -m mcp_context_graph [PROJECT_PATH]
"""

from mcp_context_graph.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
