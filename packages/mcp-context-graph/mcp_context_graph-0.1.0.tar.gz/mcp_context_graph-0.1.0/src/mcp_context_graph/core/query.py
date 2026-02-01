"""
QueryInterface: Graph query operations.

This module provides a query interface for the context graph including:
- find_definition(name)
- find_callers(name)
- find_callees(name)
- find_imports(name)
- get_context_subgraph(name, depth)

Note: Most query methods are implemented directly on ContextGraph.
This module provides additional query utilities and a facade interface.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp_context_graph.core.graph import ContextGraph
    from mcp_context_graph.core.node import GraphNode

logger = logging.getLogger(__name__)


@dataclass
class QueryResult:
    """
    Result of a graph query.

    Attributes:
        nodes: List of nodes matching the query.
        query_name: Name of the query that was executed.
        total_matches: Total number of matches found.
    """

    nodes: list[GraphNode]
    query_name: str
    total_matches: int

    @property
    def empty(self) -> bool:
        """Return True if no matches found."""
        return len(self.nodes) == 0

    @property
    def first(self) -> GraphNode | None:
        """Return the first match, or None."""
        return self.nodes[0] if self.nodes else None


class QueryInterface:
    """
    High-level query interface for the context graph.

    Provides a facade over ContextGraph methods with additional
    convenience features like filtering and sorting.

    Example:
        graph = ContextGraph()
        # ... populate graph ...
        query = QueryInterface(graph)

        result = query.find_symbol("my_function")
        if not result.empty:
            print(f"Found {result.total_matches} matches")
    """

    __slots__ = ("_graph",)

    def __init__(self, graph: ContextGraph) -> None:
        """
        Initialize the query interface.

        Args:
            graph: The ContextGraph to query.
        """
        self._graph = graph

    @property
    def graph(self) -> ContextGraph:
        """Return the underlying graph."""
        return self._graph

    def find_symbol(
        self,
        name: str,
        language: str | None = None,
    ) -> QueryResult:
        """
        Find all symbols matching a name.

        Searches functions, classes, and methods.

        Args:
            name: The symbol name to search for.
            language: Optional language filter.

        Returns:
            QueryResult with matching nodes.
        """
        definitions = self._graph.find_definitions(name)

        # Filter by language if specified
        if language:
            definitions = [d for d in definitions if d.language == language]

        logger.debug(
            "find_symbol(%r, language=%s): %d matches",
            name,
            language,
            len(definitions),
        )

        return QueryResult(
            nodes=definitions,
            query_name="find_symbol",
            total_matches=len(definitions),
        )

    def find_callers(self, name: str) -> QueryResult:
        """
        Find all callers of a function/method.

        Args:
            name: The function/method name.

        Returns:
            QueryResult with calling nodes.
        """
        callers = self._graph.find_callers(name)

        return QueryResult(
            nodes=callers,
            query_name="find_callers",
            total_matches=len(callers),
        )

    def find_callees(self, name: str) -> QueryResult:
        """
        Find all functions called by a function/method.

        Args:
            name: The function/method name.

        Returns:
            QueryResult with called nodes.
        """
        callees = self._graph.find_callees(name)

        return QueryResult(
            nodes=callees,
            query_name="find_callees",
            total_matches=len(callees),
        )

    def find_imports(self, name: str) -> QueryResult:
        """
        Find import statements for a module/symbol.

        Args:
            name: The module or symbol name.

        Returns:
            QueryResult with import nodes.
        """
        imports = self._graph.find_imports(name)

        return QueryResult(
            nodes=imports,
            query_name="find_imports",
            total_matches=len(imports),
        )

    def find_importers(self, name: str) -> QueryResult:
        """
        Find all modules that import a symbol.

        Args:
            name: The module or symbol name.

        Returns:
            QueryResult with importer nodes.
        """
        importers = self._graph.find_importers(name)

        return QueryResult(
            nodes=importers,
            query_name="find_importers",
            total_matches=len(importers),
        )

    def get_context(
        self,
        name: str,
        depth: int = 1,
    ) -> QueryResult:
        """
        Get context subgraph around a symbol.

        Args:
            name: The center symbol name.
            depth: Number of edge hops to include.

        Returns:
            QueryResult with nodes in the context.
        """
        context = self._graph.get_context_subgraph(name, depth=depth)

        return QueryResult(
            nodes=context,
            query_name="get_context",
            total_matches=len(context),
        )

    def find_by_file(self, file_path: str) -> QueryResult:
        """
        Find all nodes in a specific file.

        Args:
            file_path: The file path to search.

        Returns:
            QueryResult with nodes from that file.
        """
        nodes = self._graph.find_by_file(file_path)

        return QueryResult(
            nodes=nodes,
            query_name="find_by_file",
            total_matches=len(nodes),
        )

    def search(
        self,
        pattern: str,
        language: str | None = None,
    ) -> QueryResult:
        """
        Search for symbols matching a pattern.

        Uses simple substring matching. For more advanced patterns,
        use direct graph queries.

        Args:
            pattern: String pattern to search for.
            language: Optional language filter.

        Returns:
            QueryResult with matching nodes.
        """
        matches: list[GraphNode] = []
        pattern_lower = pattern.lower()

        for node in self._graph.iter_nodes():
            # Search in name and qualified_name
            if (
                pattern_lower in node.name.lower()
                or pattern_lower in node.qualified_name.lower()
            ) and (language is None or node.language == language):
                matches.append(node)

        logger.debug(
            "search(%r, language=%s): %d matches",
            pattern,
            language,
            len(matches),
        )

        return QueryResult(
            nodes=matches,
            query_name="search",
            total_matches=len(matches),
        )

    def __repr__(self) -> str:
        """Return string representation."""
        return f"QueryInterface(graph_nodes={self._graph.node_count})"
