"""
GraphEdge Pydantic V2 model for graph edges.
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict

from mcp_context_graph.core.node import SourceLocation


class EdgeType(str, Enum):
    """Types of edges in the context graph."""

    CALLS = "calls"
    IMPORTS = "imports"
    DEFINES = "defines"
    INHERITS = "inherits"
    CONTAINS = "contains"


class GraphEdge(BaseModel):
    """
    An edge in the context graph representing a relationship between code elements.
    """

    source_id: str
    target_id: str
    type: EdgeType
    location: SourceLocation | None = None

    model_config = ConfigDict(frozen=True)
