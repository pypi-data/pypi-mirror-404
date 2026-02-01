"""
MCP Resource Providers.

This module defines resource providers for exposing graph data
via the MCP protocol. Resources provide read-only access to:
- Graph statistics
- Node listings
- File-based queries
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mcp_context_graph.ingest.ingestor import Ingestor

logger = logging.getLogger(__name__)


@dataclass
class ResourceDefinition:
    """
    Definition of an MCP resource.

    Attributes:
        uri: The resource URI pattern.
        name: Human-readable name.
        description: Detailed description.
        mime_type: MIME type of the response.
    """

    uri: str
    name: str
    description: str
    mime_type: str = "application/json"


class GraphStatsResource:
    """
    Resource provider for graph statistics.

    Provides read-only access to:
    - Node count
    - Edge count
    - Language breakdown
    - Node type breakdown
    """

    URI = "graph://stats"
    NAME = "Graph Statistics"
    DESCRIPTION = "Statistics about the context graph (nodes, edges, languages)"

    def __init__(self, ingestor: Ingestor) -> None:
        """Initialize with ingestor reference."""
        self._ingestor = ingestor

    @property
    def definition(self) -> ResourceDefinition:
        """Return resource definition."""
        return ResourceDefinition(
            uri=self.URI,
            name=self.NAME,
            description=self.DESCRIPTION,
        )

    def get_data(self) -> dict[str, Any]:
        """
        Get graph statistics.

        Returns:
            Dictionary with graph statistics.
        """
        graph = self._ingestor.graph

        # Count nodes by type
        type_counts: dict[str, int] = {}
        language_counts: dict[str, int] = {}

        for node in graph.iter_nodes():
            # Count by type
            type_name = node.type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

            # Count by language
            lang = node.language
            language_counts[lang] = language_counts.get(lang, 0) + 1

        return {
            "node_count": graph.node_count,
            "edge_count": graph.edge_count,
            "nodes_by_type": type_counts,
            "nodes_by_language": language_counts,
        }


class GraphNodesResource:
    """
    Resource provider for listing graph nodes.

    Provides a paginated list of all nodes in the graph.
    """

    URI = "graph://nodes"
    NAME = "Graph Nodes"
    DESCRIPTION = "List of all nodes in the context graph"

    def __init__(self, ingestor: Ingestor) -> None:
        """Initialize with ingestor reference."""
        self._ingestor = ingestor

    @property
    def definition(self) -> ResourceDefinition:
        """Return resource definition."""
        return ResourceDefinition(
            uri=self.URI,
            name=self.NAME,
            description=self.DESCRIPTION,
        )

    def get_data(self, limit: int = 100, offset: int = 0) -> dict[str, Any]:
        """
        Get paginated node list.

        Args:
            limit: Maximum nodes to return.
            offset: Number of nodes to skip.

        Returns:
            Dictionary with node data and pagination info.
        """
        graph = self._ingestor.graph
        all_nodes = list(graph.iter_nodes())

        total = len(all_nodes)
        paginated = all_nodes[offset : offset + limit]

        nodes_data = [
            {
                "id": n.id,
                "name": n.name,
                "type": n.type.value,
                "qualified_name": n.qualified_name,
                "language": n.language,
                "file": n.location.file_path,
                "line": n.location.start_line,
            }
            for n in paginated
        ]

        return {
            "nodes": nodes_data,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total,
        }


class FileNodesResource:
    """
    Resource provider for nodes in a specific file.

    URI pattern: file://{path}
    """

    URI_PATTERN = "file://{path}"
    NAME = "File Nodes"
    DESCRIPTION = "Nodes defined in a specific source file"

    def __init__(self, ingestor: Ingestor) -> None:
        """Initialize with ingestor reference."""
        self._ingestor = ingestor

    @property
    def definition(self) -> ResourceDefinition:
        """Return resource definition."""
        return ResourceDefinition(
            uri=self.URI_PATTERN,
            name=self.NAME,
            description=self.DESCRIPTION,
        )

    def get_data(self, file_path: str) -> dict[str, Any]:
        """
        Get nodes defined in a file.

        Args:
            file_path: Relative path to the file.

        Returns:
            Dictionary with file nodes.
        """
        graph = self._ingestor.graph
        nodes = graph.find_by_file(file_path)

        return {
            "file_path": file_path,
            "node_count": len(nodes),
            "nodes": [
                {
                    "id": n.id,
                    "name": n.name,
                    "type": n.type.value,
                    "signature": n.signature,
                    "line": n.location.start_line,
                }
                for n in nodes
            ],
        }


class ResourceRegistry:
    """
    Registry for MCP resources.

    Manages available resources and handles lookups.
    """

    __slots__ = ("_ingestor", "_resources")

    def __init__(self, ingestor: Ingestor) -> None:
        """
        Initialize with ingestor.

        Args:
            ingestor: The Ingestor instance.
        """
        self._ingestor = ingestor
        self._resources: dict[str, Any] = {}
        self._register_built_in_resources()

    def _register_built_in_resources(self) -> None:
        """Register all built-in resources."""
        self._resources["graph://stats"] = GraphStatsResource(self._ingestor)
        self._resources["graph://nodes"] = GraphNodesResource(self._ingestor)
        # File resources use a pattern, handled separately

    def get_resource(self, uri: str) -> Any | None:
        """
        Get a resource by URI.

        Args:
            uri: The resource URI.

        Returns:
            The resource provider, or None if not found.
        """
        # Exact match
        if uri in self._resources:
            return self._resources[uri]

        # Pattern match for file:// URIs
        if uri.startswith("file://"):
            return FileNodesResource(self._ingestor)

        return None

    def get_resource_data(self, uri: str) -> dict[str, Any]:
        """
        Get data for a resource.

        Args:
            uri: The resource URI.

        Returns:
            Resource data dictionary.
        """
        resource = self.get_resource(uri)
        if resource is None:
            return {"error": f"Unknown resource: {uri}"}

        # Handle different resource types
        if isinstance(resource, (GraphStatsResource, GraphNodesResource)):
            return resource.get_data()
        elif isinstance(resource, FileNodesResource):
            file_path = uri[7:]  # Remove "file://"
            return resource.get_data(file_path)
        else:
            return {"error": "Unknown resource type"}

    def list_resources(self) -> list[ResourceDefinition]:
        """
        List all available resources.

        Returns:
            List of resource definitions.
        """
        definitions = []

        for resource in self._resources.values():
            definitions.append(resource.definition)

        # Add file resource pattern
        definitions.append(FileNodesResource(self._ingestor).definition)

        return definitions
