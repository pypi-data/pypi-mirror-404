"""
MCPServer: Main MCP server implementation.

This module implements the MCP server using stdio transport
for communication with AI agents like Cline/Claude Desktop.

CRITICAL: NO print() statements - use logger only (outputs to stderr).
The stdout stream is reserved exclusively for JSON-RPC protocol messages.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from mcp_context_graph.ingest.ingestor import Ingestor
from mcp_context_graph.mcp.tools import (
    DebugDumpGraphInput,
    ExpandSourceInput,
    FindCallersInput,
    FindSymbolInput,
    GetContextInput,
    IndexProjectInput,
    tool_debug_dump_graph,
    tool_expand_source,
    tool_find_callers,
    tool_find_symbol,
    tool_get_context,
    tool_index_project,
)

logger = logging.getLogger(__name__)


class MCPContextGraphServer:
    """
    MCP Server wrapper for the Context Graph.

    This class manages the global state (Ingestor, Graph) and provides
    the MCP server instance with all tool registrations.

    Attributes:
        project_root: The root directory being indexed.
        ingestor: The Ingestor instance managing the graph.
        server: The MCP Server instance.
    """

    def __init__(self, project_root: Path) -> None:
        """
        Initialize the MCP server.

        Args:
            project_root: Path to the project directory to index.
        """
        self.project_root = project_root.resolve()
        self.ingestor = Ingestor(self.project_root)
        self.server = Server("mcp-context-graph")

        # Register all tools
        self._register_tools()
        self._register_handlers()

        logger.info("MCPContextGraphServer initialized for: %s", self.project_root)

    def _register_tools(self) -> None:
        """Register all available tools with the MCP server."""

        @self.server.list_tools()  # type: ignore[no-untyped-call, untyped-decorator]
        async def list_tools() -> list[Tool]:
            """Return the list of available tools."""
            return [
                Tool(
                    name="index_project",
                    description=(
                        "Index a project directory to build the code graph. "
                        "This scans all Python, TypeScript, and JavaScript files, "
                        "extracts function/class definitions, and builds a dependency graph. "
                        "Run this first before using other tools."
                    ),
                    inputSchema=IndexProjectInput.model_json_schema(),
                ),
                Tool(
                    name="find_symbol",
                    description=(
                        "Find function, class, or method definitions by name. "
                        "Returns all matching definitions with their locations and signatures. "
                        "Optionally filter by language or include call sites."
                    ),
                    inputSchema=FindSymbolInput.model_json_schema(),
                ),
                Tool(
                    name="find_callers",
                    description=(
                        "Find all locations in the codebase that call a specific function or method. "
                        "Useful for understanding how a function is used and what depends on it."
                    ),
                    inputSchema=FindCallersInput.model_json_schema(),
                ),
                Tool(
                    name="get_context",
                    description=(
                        "Get the contextual neighborhood around a symbol. "
                        "Returns the symbol plus all connected nodes within a specified depth. "
                        "Useful for understanding the dependencies and usage patterns of a symbol."
                    ),
                    inputSchema=GetContextInput.model_json_schema(),
                ),
                Tool(
                    name="expand_source",
                    description=(
                        "Expand a minified symbol to its full original source code. "
                        "Uses source maps to map from the compact signature back to the full definition. "
                        "Useful when you need to see the complete implementation."
                    ),
                    inputSchema=ExpandSourceInput.model_json_schema(),
                ),
                Tool(
                    name="debug_dump_graph",
                    description=(
                        "DEBUG: Dump the entire graph structure for visualization. "
                        "Returns the graph in Mermaid diagram, JSON, or Graphviz DOT format. "
                        "Useful for debugging and understanding the graph structure."
                    ),
                    inputSchema=DebugDumpGraphInput.model_json_schema(),
                ),
            ]

    def _register_handlers(self) -> None:
        """Register tool call handlers."""

        @self.server.call_tool()  # type: ignore[untyped-decorator]
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            """
            Handle tool calls from the MCP client.

            Args:
                name: The name of the tool to call.
                arguments: The arguments passed to the tool.

            Returns:
                List of TextContent with the tool response.
            """
            logger.info("Tool called: %s with arguments: %s", name, arguments)

            try:
                result = self._dispatch_tool(name, arguments)
                response_text = json.dumps(result, indent=2, default=str)
                return [TextContent(type="text", text=response_text)]

            except Exception as e:
                logger.exception("Tool %s failed with error: %s", name, e)
                error_response = {
                    "success": False,
                    "error": str(e),
                    "tool": name,
                }
                return [
                    TextContent(type="text", text=json.dumps(error_response, indent=2))
                ]

    def _dispatch_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """
        Dispatch a tool call to the appropriate handler.

        Args:
            name: The tool name.
            arguments: The tool arguments.

        Returns:
            The tool result as a dictionary.

        Raises:
            ValueError: If the tool name is unknown.
        """
        if name == "index_project":
            return tool_index_project(
                IndexProjectInput(**arguments),
                self.ingestor,
                self.project_root,
            )

        if name == "find_symbol":
            return tool_find_symbol(
                FindSymbolInput(**arguments),
                self.ingestor,
            )

        if name == "find_callers":
            return tool_find_callers(
                FindCallersInput(**arguments),
                self.ingestor,
            )

        if name == "get_context":
            return tool_get_context(
                GetContextInput(**arguments),
                self.ingestor,
            )

        if name == "expand_source":
            return tool_expand_source(
                ExpandSourceInput(**arguments),
                self.ingestor,
            )

        if name == "debug_dump_graph":
            return tool_debug_dump_graph(
                DebugDumpGraphInput(**arguments),
                self.ingestor,
            )

        raise ValueError(f"Unknown tool: {name}")

    async def run(self) -> None:
        """
        Run the MCP server using stdio transport.

        This method blocks until the server is shut down.
        """
        logger.info("Starting MCP server on stdio...")

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options(),
            )


async def run_server(project_root: Path) -> None:
    """
    Create and run the MCP server.

    This is the main entry point for starting the server.

    Args:
        project_root: Path to the project directory to index.
    """
    server = MCPContextGraphServer(project_root)
    await server.run()
