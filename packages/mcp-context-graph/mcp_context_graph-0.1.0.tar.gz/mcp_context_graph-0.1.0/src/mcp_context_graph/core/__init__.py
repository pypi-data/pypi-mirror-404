"""
Core library module (framework-agnostic).

Contains:
- GraphNode: Pydantic V2 model for graph nodes
- GraphEdge: Pydantic V2 model for graph edges
- ContextGraph: NetworkX wrapper for graph operations
- QueryInterface: Graph query operations
"""

from mcp_context_graph.core.edge import EdgeType, GraphEdge
from mcp_context_graph.core.graph import ContextGraph
from mcp_context_graph.core.node import GraphNode, NodeType, SourceLocation

__all__ = [
    "NodeType",
    "GraphNode",
    "SourceLocation",
    "EdgeType",
    "GraphEdge",
    "ContextGraph",
]
