"""
MCP Request Handlers.

This module contains the request handler logic for the MCP server.
Handlers process incoming tool calls and resource requests.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

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


class ToolHandler:
    """
    Handler for MCP tool requests.

    Routes tool calls to the appropriate implementation functions
    and handles error wrapping.
    """

    __slots__ = ("_ingestor", "_project_root")

    def __init__(self, ingestor: Ingestor, project_root: Path) -> None:
        """
        Initialize the tool handler.

        Args:
            ingestor: The Ingestor instance for graph operations.
            project_root: The default project root path.
        """
        self._ingestor = ingestor
        self._project_root = project_root

    async def handle_tool(
        self,
        name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Handle a tool call request.

        Args:
            name: The tool name.
            arguments: The tool arguments.

        Returns:
            Tool result as a dictionary.

        Raises:
            ValueError: If tool is unknown.
        """
        logger.info("Handling tool call: %s", name)

        try:
            if name == "index_project":
                return tool_index_project(
                    IndexProjectInput(**arguments), self._ingestor, self._project_root
                )

            elif name == "find_symbol":
                return tool_find_symbol(FindSymbolInput(**arguments), self._ingestor)

            elif name == "find_callers":
                return tool_find_callers(FindCallersInput(**arguments), self._ingestor)

            elif name == "get_context":
                return tool_get_context(GetContextInput(**arguments), self._ingestor)

            elif name == "expand_source":
                return tool_expand_source(
                    ExpandSourceInput(**arguments), self._ingestor
                )

            elif name == "debug_dump_graph":
                return tool_debug_dump_graph(
                    DebugDumpGraphInput(**arguments), self._ingestor
                )

            else:
                msg = f"Unknown tool: {name}"
                logger.warning(msg)
                return {"success": False, "error": msg}

        except Exception as e:
            logger.exception("Error handling tool %s: %s", name, e)
            return {
                "success": False,
                "error": f"Tool execution failed: {e!s}",
            }

    def get_tool_names(self) -> list[str]:
        """Return list of available tool names."""
        return [
            "index_project",
            "find_symbol",
            "find_callers",
            "get_context",
            "expand_source",
            "debug_dump_graph",
        ]


class ResourceHandler:
    """
    Handler for MCP resource requests.

    Provides access to graph data as resources.
    """

    __slots__ = ("_ingestor",)

    def __init__(self, ingestor: Ingestor) -> None:
        """
        Initialize the resource handler.

        Args:
            ingestor: The Ingestor instance.
        """
        self._ingestor = ingestor

    async def handle_resource(
        self,
        uri: str,
    ) -> dict[str, Any]:
        """
        Handle a resource request.

        Args:
            uri: The resource URI.

        Returns:
            Resource data as a dictionary.
        """
        logger.info("Handling resource request: %s", uri)

        # Parse URI
        if uri.startswith("graph://"):
            return await self._handle_graph_resource(uri)
        elif uri.startswith("file://"):
            return await self._handle_file_resource(uri)
        else:
            return {
                "success": False,
                "error": f"Unknown resource scheme: {uri}",
            }

    async def _handle_graph_resource(self, uri: str) -> dict[str, Any]:
        """Handle graph:// resources."""
        path = uri[8:]  # Remove "graph://"

        graph = self._ingestor.graph

        if path == "stats":
            return {
                "success": True,
                "data": {
                    "node_count": graph.node_count,
                    "edge_count": graph.edge_count,
                },
            }
        elif path == "nodes":
            nodes = [
                {"id": n.id, "name": n.name, "type": n.type.value}
                for n in graph.iter_nodes()
            ]
            return {"success": True, "data": nodes}
        else:
            return {"success": False, "error": f"Unknown graph resource: {path}"}

    async def _handle_file_resource(self, uri: str) -> dict[str, Any]:
        """Handle file:// resources."""
        file_path = uri[7:]  # Remove "file://"

        nodes = self._ingestor.graph.find_by_file(file_path)
        return {
            "success": True,
            "data": [
                {
                    "id": n.id,
                    "name": n.name,
                    "type": n.type.value,
                    "signature": n.signature,
                }
                for n in nodes
            ],
        }

    def get_resource_templates(self) -> list[dict[str, str]]:
        """Return list of available resource templates."""
        return [
            {
                "uri": "graph://stats",
                "description": "Graph statistics (node/edge counts)",
            },
            {
                "uri": "graph://nodes",
                "description": "List of all nodes in the graph",
            },
            {
                "uri": "file://{path}",
                "description": "Nodes defined in a specific file",
            },
        ]
