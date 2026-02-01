"""
CLI entry point for mcp-context-graph.

Usage: mcp-context-graph [OPTIONS] [PROJECT_PATH]

This is the main entry point when running:
- uvx mcp-context-graph
- uv run mcp-context-graph
- python -m mcp_context_graph

CRITICAL: NO print() statements - use logger only.
The stdout stream is reserved exclusively for JSON-RPC protocol messages.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from mcp_context_graph import __version__, logger


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog="mcp-context-graph",
        description="MCP-Aware Context Graph: A memory layer for local AI agents.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "project_path",
        nargs="?",
        type=Path,
        default=Path.cwd(),
        help="Path to the project to index (default: current directory)",
    )
    parser.add_argument(
        "--stdio",
        action="store_true",
        default=True,
        help="Run in stdio mode for MCP communication (default)",
    )
    return parser


def main() -> int:
    """
    Main entry point for the CLI.

    Initializes the Ingestor with the project path and starts
    the MCP server using stdio transport.

    Returns:
        Exit code (0 for success, non-zero for error).
    """
    parser = create_parser()
    args = parser.parse_args()

    # Validate project path
    project_path = Path(args.project_path).resolve()

    if not project_path.exists():
        logger.error("Project path does not exist: %s", project_path)
        return 1

    if not project_path.is_dir():
        logger.error("Project path is not a directory: %s", project_path)
        return 1

    logger.info("Initializing Context Graph for %s...", project_path)

    try:
        # Import here to avoid circular imports and defer heavy loading
        from mcp_context_graph.mcp.server import run_server

        # Run the async server
        asyncio.run(run_server(project_path))
        return 0

    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
        return 0

    except Exception as e:
        logger.exception("Server failed with error: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
