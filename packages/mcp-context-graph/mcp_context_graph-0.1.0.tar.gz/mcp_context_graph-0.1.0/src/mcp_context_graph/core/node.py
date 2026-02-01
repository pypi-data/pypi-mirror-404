"""
GraphNode Pydantic V2 model for graph nodes.
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict


class NodeType(str, Enum):
    """Types of nodes in the context graph."""

    MODULE = "module"
    FUNCTION = "function"
    CLASS = "class"
    METHOD = "method"
    IMPORT = "import"
    CALL = "call"


class SourceLocation(BaseModel):
    """Source code location information."""

    file_path: str
    start_byte: int
    end_byte: int
    start_line: int
    start_column: int
    end_line: int
    end_column: int

    model_config = ConfigDict(frozen=True)


class GraphNode(BaseModel):
    """
    A node in the context graph representing a code element.

    Note: source_map_id is a reference to ProvenanceStore, not the actual SourceMap.
    This ensures clean JSON serialization of GraphNode.
    """

    id: str  # Unique hash
    type: NodeType
    name: str
    qualified_name: str  # e.g., "MyClass.my_method"
    language: str  # "python", "typescript", "javascript"
    signature: str  # Minified representation
    location: SourceLocation
    source_map_id: str | None = None  # Reference to ProvenanceStore
    parameters: str | None = None
    return_type: str | None = None
    docstring: str | None = None

    model_config = ConfigDict(frozen=True)
