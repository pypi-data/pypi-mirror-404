"""
ContextGraph: NetworkX wrapper for graph operations.

This module provides the main graph data structure that wraps NetworkX
and provides methods for adding nodes, edges, and querying the graph.

IMPORTANT: GraphNodes store `source_map_id` (string), NOT SourceMap objects.
This ensures clean JSON serialization and separation of concerns.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import TYPE_CHECKING, Any

import networkx as nx

from mcp_context_graph.core.edge import EdgeType, GraphEdge
from mcp_context_graph.core.node import GraphNode, NodeType

if TYPE_CHECKING:
    from collections.abc import Iterator

logger = logging.getLogger(__name__)


class ContextGraph:
    """
    In-memory context graph wrapping NetworkX DiGraph.

    The ContextGraph stores GraphNodes and GraphEdges representing
    code elements and their relationships. It provides efficient
    queries for finding definitions, callers, callees, and imports.

    Design Decisions:
    - Nodes store `source_map_id` (str), NOT SourceMap objects
    - ProvenanceTracker is separate and manages SourceMap objects
    - All node/edge data uses Pydantic models for validation
    - Indices maintained for O(1) name-based lookups

    Example:
        graph = ContextGraph()
        node = GraphNode(id="abc123", type=NodeType.FUNCTION, ...)
        graph.add_node(node)
        graph.find_definition("my_function")
    """

    __slots__ = (
        "_graph",
        "_name_index",
        "_qualified_name_index",
        "_type_index",
        "_file_index",
    )

    def __init__(self) -> None:
        """Initialize an empty ContextGraph."""
        self._graph: nx.DiGraph[str] = nx.DiGraph()

        # Indices for fast lookups
        # name -> set of node IDs (functions can have same name in different files)
        self._name_index: dict[str, set[str]] = defaultdict(set)
        # qualified_name -> node ID (should be unique)
        self._qualified_name_index: dict[str, str] = {}
        # NodeType -> set of node IDs
        self._type_index: dict[NodeType, set[str]] = defaultdict(set)
        # file_path -> set of node IDs
        self._file_index: dict[str, set[str]] = defaultdict(set)

        logger.debug("ContextGraph initialized")

    @property
    def node_count(self) -> int:
        """Return the number of nodes in the graph."""
        return int(self._graph.number_of_nodes())

    @property
    def edge_count(self) -> int:
        """Return the number of edges in the graph."""
        return int(self._graph.number_of_edges())

    def __len__(self) -> int:
        """Return the number of nodes."""
        return self.node_count

    def __bool__(self) -> bool:
        """Return True if graph has nodes."""
        return self.node_count > 0

    def __contains__(self, node_id: str) -> bool:
        """Check if a node ID exists in the graph."""
        return node_id in self._graph

    # -------------------------------------------------------------------------
    # Node Operations
    # -------------------------------------------------------------------------

    def add_node(self, node: GraphNode) -> None:
        """
        Add a node to the graph with Pydantic validation.

        Args:
            node: GraphNode to add. Must be a valid GraphNode instance.

        Raises:
            ValueError: If node with same ID already exists.
        """
        if node.id in self._graph:
            msg = f"Node with ID {node.id!r} already exists"
            raise ValueError(msg)

        # Store the full GraphNode model as node data
        self._graph.add_node(node.id, data=node)

        # Update indices
        self._name_index[node.name].add(node.id)
        self._qualified_name_index[node.qualified_name] = node.id
        self._type_index[node.type].add(node.id)
        self._file_index[node.location.file_path].add(node.id)

        logger.debug(
            "Added node: %s (type=%s, name=%r)",
            node.id,
            node.type.value,
            node.name,
        )

    def get_node(self, node_id: str) -> GraphNode | None:
        """
        Get a node by its ID.

        Args:
            node_id: The unique node identifier.

        Returns:
            The GraphNode if found, None otherwise.
        """
        if node_id not in self._graph:
            return None
        data: Any = self._graph.nodes[node_id].get("data")
        if isinstance(data, GraphNode):
            return data
        return None

    def remove_node(self, node_id: str) -> bool:
        """
        Remove a node from the graph.

        Args:
            node_id: The node ID to remove.

        Returns:
            True if node was removed, False if not found.
        """
        if node_id not in self._graph:
            return False

        node = self.get_node(node_id)
        if node:
            # Remove from indices
            self._name_index[node.name].discard(node_id)
            if not self._name_index[node.name]:
                del self._name_index[node.name]

            if self._qualified_name_index.get(node.qualified_name) == node_id:
                del self._qualified_name_index[node.qualified_name]

            self._type_index[node.type].discard(node_id)
            if not self._type_index[node.type]:
                del self._type_index[node.type]

            self._file_index[node.location.file_path].discard(node_id)
            if not self._file_index[node.location.file_path]:
                del self._file_index[node.location.file_path]

        self._graph.remove_node(node_id)
        logger.debug("Removed node: %s", node_id)
        return True

    def iter_nodes(self) -> Iterator[GraphNode]:
        """Iterate over all nodes in the graph."""
        for node_id in self._graph.nodes:
            node = self.get_node(node_id)
            if node:
                yield node

    def get_all_nodes(self) -> list[GraphNode]:
        """Get all nodes in the graph."""
        return list(self.iter_nodes())

    # -------------------------------------------------------------------------
    # Edge Operations
    # -------------------------------------------------------------------------

    def add_edge(self, edge: GraphEdge) -> None:
        """
        Add an edge to the graph with Pydantic validation.

        Args:
            edge: GraphEdge to add. Source and target nodes must exist.

        Raises:
            ValueError: If source or target node doesn't exist.
        """
        if edge.source_id not in self._graph:
            msg = f"Source node {edge.source_id!r} doesn't exist"
            raise ValueError(msg)

        if edge.target_id not in self._graph:
            msg = f"Target node {edge.target_id!r} doesn't exist"
            raise ValueError(msg)

        # Store edge with type attribute
        self._graph.add_edge(
            edge.source_id,
            edge.target_id,
            type=edge.type,
            data=edge,
        )

        logger.debug(
            "Added edge: %s -[%s]-> %s",
            edge.source_id,
            edge.type.value,
            edge.target_id,
        )

    def get_edge(self, source_id: str, target_id: str) -> GraphEdge | None:
        """
        Get an edge between two nodes.

        Args:
            source_id: Source node ID.
            target_id: Target node ID.

        Returns:
            The GraphEdge if found, None otherwise.
        """
        if not self._graph.has_edge(source_id, target_id):
            return None
        data: Any = self._graph.edges[source_id, target_id].get("data")
        if isinstance(data, GraphEdge):
            return data
        return None

    def has_edge(self, source_id: str, target_id: str) -> bool:
        """Check if an edge exists between two nodes."""
        return bool(self._graph.has_edge(source_id, target_id))

    def iter_edges(self) -> Iterator[GraphEdge]:
        """Iterate over all edges in the graph."""
        for source, target in self._graph.edges:
            edge = self.get_edge(source, target)
            if edge:
                yield edge

    def get_all_edges(self) -> list[GraphEdge]:
        """Get all edges in the graph."""
        return list(self.iter_edges())

    # -------------------------------------------------------------------------
    # Query Methods - Index Lookups
    # -------------------------------------------------------------------------

    def find_definition(self, name: str) -> GraphNode | None:
        """
        Find a function/class definition by name.

        Uses the name index for O(1) lookup. If multiple definitions
        share the same name, returns the first one found.

        Args:
            name: The symbol name to search for.

        Returns:
            The GraphNode definition if found, None otherwise.
        """
        node_ids = self._name_index.get(name, set())

        # Filter to only definition types (FUNCTION, CLASS, METHOD)
        definition_types = {NodeType.FUNCTION, NodeType.CLASS, NodeType.METHOD}

        for node_id in node_ids:
            node = self.get_node(node_id)
            if node and node.type in definition_types:
                logger.debug("find_definition(%r) -> %s", name, node_id)
                return node

        logger.debug("find_definition(%r) -> None", name)
        return None

    def find_definitions(self, name: str) -> list[GraphNode]:
        """
        Find all definitions matching a name.

        Args:
            name: The symbol name to search for.

        Returns:
            List of matching GraphNode definitions.
        """
        node_ids = self._name_index.get(name, set())
        definition_types = {NodeType.FUNCTION, NodeType.CLASS, NodeType.METHOD}

        results: list[GraphNode] = []
        for node_id in node_ids:
            node = self.get_node(node_id)
            if node and node.type in definition_types:
                results.append(node)

        logger.debug("find_definitions(%r) -> %d results", name, len(results))
        return results

    def find_by_qualified_name(self, qualified_name: str) -> GraphNode | None:
        """
        Find a node by its fully qualified name.

        Args:
            qualified_name: The fully qualified name (e.g., "MyClass.my_method").

        Returns:
            The GraphNode if found, None otherwise.
        """
        node_id = self._qualified_name_index.get(qualified_name)
        if node_id:
            return self.get_node(node_id)
        return None

    def find_by_type(self, node_type: NodeType) -> list[GraphNode]:
        """
        Find all nodes of a specific type.

        Args:
            node_type: The NodeType to filter by.

        Returns:
            List of matching GraphNodes.
        """
        node_ids = self._type_index.get(node_type, set())
        nodes = [self.get_node(nid) for nid in node_ids]
        return [n for n in nodes if n is not None]

    def find_by_file(self, file_path: str) -> list[GraphNode]:
        """
        Find all nodes in a specific file.

        Args:
            file_path: The file path to filter by.

        Returns:
            List of GraphNodes defined in that file.
        """
        node_ids = self._file_index.get(file_path, set())
        nodes = [self.get_node(nid) for nid in node_ids]
        return [n for n in nodes if n is not None]

    def remove_nodes_by_file(self, file_path: str) -> int:
        """
        Remove all nodes associated with a specific file.

        This method finds all nodes associated with the given file path
        and removes them (along with their incident edges) from the graph.
        This is required for lazy re-ingestion to clear "old" data before
        re-ingesting a modified file.

        Args:
            file_path: The file path whose nodes should be removed.

        Returns:
            Number of nodes removed.
        """
        # Get a copy of the node IDs to avoid modifying dict during iteration
        node_ids = list(self._file_index.get(file_path, set()))

        if not node_ids:
            logger.debug("remove_nodes_by_file(%r): no nodes found", file_path)
            return 0

        removed_count = 0
        for node_id in node_ids:
            if self.remove_node(node_id):
                removed_count += 1

        logger.debug(
            "remove_nodes_by_file(%r): removed %d nodes",
            file_path,
            removed_count,
        )
        return removed_count

    # -------------------------------------------------------------------------
    # Query Methods - Graph Traversals
    # -------------------------------------------------------------------------

    def find_callers(self, name: str) -> list[GraphNode]:
        """
        Find all nodes that call a function/method with the given name.

        Uses reverse edge traversal to find incoming CALLS edges.

        Args:
            name: The function/method name to find callers for.

        Returns:
            List of GraphNodes that call this function.
        """
        # First find the definition
        definition = self.find_definition(name)
        if not definition:
            logger.debug("find_callers(%r): definition not found", name)
            return []

        callers: list[GraphNode] = []
        # Get all incoming edges of type CALLS
        for source_id, _, edge_data in self._graph.in_edges(definition.id, data=True):
            if edge_data.get("type") == EdgeType.CALLS:
                caller = self.get_node(source_id)
                if caller:
                    callers.append(caller)

        logger.debug("find_callers(%r) -> %d results", name, len(callers))
        return callers

    def find_callees(self, name: str) -> list[GraphNode]:
        """
        Find all functions/methods called by a node with the given name.

        Uses forward edge traversal to find outgoing CALLS edges.

        Args:
            name: The function/method name to find callees for.

        Returns:
            List of GraphNodes that are called by this function.
        """
        definition = self.find_definition(name)
        if not definition:
            logger.debug("find_callees(%r): definition not found", name)
            return []

        callees: list[GraphNode] = []
        for _, target_id, edge_data in self._graph.out_edges(definition.id, data=True):
            if edge_data.get("type") == EdgeType.CALLS:
                callee = self.get_node(target_id)
                if callee:
                    callees.append(callee)

        logger.debug("find_callees(%r) -> %d results", name, len(callees))
        return callees

    def find_imports(self, name: str) -> list[GraphNode]:
        """
        Find all import statements for a given module/symbol name.

        Searches nodes of type IMPORT matching the name, or finds
        nodes with incoming IMPORTS edges to the target.

        Args:
            name: The module or symbol name to find imports for.

        Returns:
            List of import GraphNodes.
        """
        results: list[GraphNode] = []

        # Find direct import nodes with this name
        node_ids = self._name_index.get(name, set())
        for node_id in node_ids:
            node = self.get_node(node_id)
            if node and node.type == NodeType.IMPORT:
                results.append(node)

        # Also check for IMPORTS edges pointing to definitions
        definition = self.find_definition(name)
        if definition:
            for source_id, _, edge_data in self._graph.in_edges(
                definition.id, data=True
            ):
                if edge_data.get("type") == EdgeType.IMPORTS:
                    importer = self.get_node(source_id)
                    if importer and importer not in results:
                        results.append(importer)

        logger.debug("find_imports(%r) -> %d results", name, len(results))
        return results

    def find_importers(self, name: str) -> list[GraphNode]:
        """
        Find all nodes that import a module/symbol.

        Args:
            name: The module or symbol name to find importers for.

        Returns:
            List of GraphNodes (modules/files) that import this symbol.
        """
        # Find the definition/module node
        target_nodes: list[GraphNode] = []

        # Check if it's a direct module
        node_ids = self._name_index.get(name, set())
        for node_id in node_ids:
            node = self.get_node(node_id)
            if node and node.type == NodeType.MODULE:
                target_nodes.append(node)

        # Also check definitions
        definition = self.find_definition(name)
        if definition:
            target_nodes.append(definition)

        importers: list[GraphNode] = []
        for target in target_nodes:
            for source_id, _, edge_data in self._graph.in_edges(target.id, data=True):
                if edge_data.get("type") == EdgeType.IMPORTS:
                    importer = self.get_node(source_id)
                    if importer and importer not in importers:
                        importers.append(importer)

        logger.debug("find_importers(%r) -> %d results", name, len(importers))
        return importers

    def get_context_subgraph(
        self,
        name: str,
        depth: int = 1,
    ) -> list[GraphNode]:
        """
        Get contextual subgraph around a symbol.

        Returns the node plus all nodes within `depth` edges
        in any direction.

        Args:
            name: The symbol name to center the subgraph on.
            depth: How many edge hops to include. Default 1.

        Returns:
            List of GraphNodes in the context subgraph.
        """
        center = self.find_definition(name)
        if not center:
            return []

        # Use BFS to find all nodes within depth
        visited = {center.id}
        current_level = {center.id}

        for _ in range(depth):
            next_level: set[str] = set()
            for node_id in current_level:
                # Outgoing edges
                for _, target_id in self._graph.out_edges(node_id):
                    if target_id not in visited:
                        next_level.add(target_id)
                        visited.add(target_id)

                # Incoming edges
                for source_id, _ in self._graph.in_edges(node_id):
                    if source_id not in visited:
                        next_level.add(source_id)
                        visited.add(source_id)

            current_level = next_level

        nodes = [self.get_node(nid) for nid in visited]
        result = [n for n in nodes if n is not None]
        logger.debug(
            "get_context_subgraph(%r, depth=%d) -> %d nodes",
            name,
            depth,
            len(result),
        )
        return result

    # -------------------------------------------------------------------------
    # Serialization & Visualization
    # -------------------------------------------------------------------------

    def to_mermaid(
        self,
        max_nodes: int | None = 50,
        include_edges: bool = True,
    ) -> str:
        """
        Generate a Mermaid diagram representation of the graph.

        Args:
            max_nodes: Maximum nodes to include. None for all nodes.
            include_edges: Whether to include edge relationships.

        Returns:
            Mermaid diagram string (flowchart LR format).
        """
        lines: list[str] = ["graph LR"]

        # Collect nodes
        nodes = list(self.iter_nodes())
        if max_nodes and len(nodes) > max_nodes:
            nodes = nodes[:max_nodes]
            lines.append(f"    %% Showing {max_nodes} of {self.node_count} nodes")

        # Track node IDs for edge filtering
        included_ids = {n.id for n in nodes}

        # Generate node definitions
        # Use short IDs for readability
        id_map: dict[str, str] = {}
        for i, node in enumerate(nodes):
            short_id = f"n{i}"
            id_map[node.id] = short_id

            # Create label with name, type, and language
            label = f"{node.name}<br/>{node.type.value}<br/>{node.language}"
            # Escape special characters
            label = label.replace('"', "'")
            lines.append(f'    {short_id}["{label}"]')

        # Generate edges
        if include_edges:
            for edge in self.iter_edges():
                if edge.source_id in included_ids and edge.target_id in included_ids:
                    src = id_map.get(edge.source_id)
                    tgt = id_map.get(edge.target_id)
                    if src and tgt:
                        edge_label = edge.type.value.upper()
                        lines.append(f"    {src} -->|{edge_label}| {tgt}")

        return "\n".join(lines)

    def to_json(
        self,
        max_nodes: int | None = None,
        include_edges: bool = True,
    ) -> str:
        """
        Generate JSON representation of the graph.

        Args:
            max_nodes: Maximum nodes to include. None for all.
            include_edges: Whether to include edges.

        Returns:
            JSON string representation.
        """
        import json

        nodes = list(self.iter_nodes())
        if max_nodes and len(nodes) > max_nodes:
            nodes = nodes[:max_nodes]

        included_ids = {n.id for n in nodes}

        # Build result dict with explicit types
        edges_list: list[dict[str, Any]] = []
        stats: dict[str, int] = {
            "total_nodes": self.node_count,
            "total_edges": self.edge_count,
            "included_nodes": len(nodes),
        }

        if include_edges:
            for edge in self.iter_edges():
                if edge.source_id in included_ids and edge.target_id in included_ids:
                    edges_list.append(edge.model_dump())
            stats["included_edges"] = len(edges_list)

        result: dict[str, Any] = {
            "nodes": [n.model_dump() for n in nodes],
            "edges": edges_list,
            "stats": stats,
        }

        return json.dumps(result, indent=2, default=str)

    def to_dot(
        self,
        max_nodes: int | None = 50,
        include_edges: bool = True,
    ) -> str:
        """
        Generate Graphviz DOT representation of the graph.

        Args:
            max_nodes: Maximum nodes to include. None for all.
            include_edges: Whether to include edges.

        Returns:
            DOT format string for Graphviz.
        """
        lines: list[str] = ["digraph ContextGraph {"]
        lines.append("    rankdir=LR;")
        lines.append("    node [shape=box, style=filled, fillcolor=lightblue];")

        nodes = list(self.iter_nodes())
        if max_nodes and len(nodes) > max_nodes:
            nodes = nodes[:max_nodes]

        included_ids = {n.id for n in nodes}
        id_map: dict[str, str] = {}

        for i, node in enumerate(nodes):
            short_id = f"n{i}"
            id_map[node.id] = short_id

            label = f"{node.name}\\n{node.type.value}\\n{node.language}"
            lines.append(f'    {short_id} [label="{label}"];')

        if include_edges:
            for edge in self.iter_edges():
                if edge.source_id in included_ids and edge.target_id in included_ids:
                    src = id_map.get(edge.source_id)
                    tgt = id_map.get(edge.target_id)
                    if src and tgt:
                        lines.append(f'    {src} -> {tgt} [label="{edge.type.value}"];')

        lines.append("}")
        return "\n".join(lines)

    def clear(self) -> None:
        """Remove all nodes and edges from the graph."""
        self._graph.clear()
        self._name_index.clear()
        self._qualified_name_index.clear()
        self._type_index.clear()
        self._file_index.clear()
        logger.debug("Graph cleared")

    def __repr__(self) -> str:
        """Return string representation."""
        return f"ContextGraph(nodes={self.node_count}, edges={self.edge_count})"
