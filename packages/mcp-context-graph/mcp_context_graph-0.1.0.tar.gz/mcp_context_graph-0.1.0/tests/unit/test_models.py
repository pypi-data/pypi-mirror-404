"""Smoke tests for Pydantic V2 models."""

import pytest
from pydantic import ValidationError

from mcp_context_graph.core.edge import EdgeType, GraphEdge
from mcp_context_graph.core.node import GraphNode, NodeType, SourceLocation
from mcp_context_graph.provenance.segment import Segment


class TestSourceLocation:
    """Tests for SourceLocation model."""

    def test_create_source_location(self) -> None:
        """Test creating a valid SourceLocation."""
        loc = SourceLocation(
            file_path="/path/to/file.py",
            start_byte=0,
            end_byte=100,
            start_line=1,
            start_column=0,
            end_line=5,
            end_column=10,
        )
        assert loc.file_path == "/path/to/file.py"
        assert loc.start_byte == 0
        assert loc.end_byte == 100

    def test_source_location_is_frozen(self) -> None:
        """Test that SourceLocation is immutable."""
        loc = SourceLocation(
            file_path="/path/to/file.py",
            start_byte=0,
            end_byte=100,
            start_line=1,
            start_column=0,
            end_line=5,
            end_column=10,
        )
        with pytest.raises(ValidationError):
            loc.file_path = "/another/path.py"  # type: ignore


class TestGraphNode:
    """Tests for GraphNode model."""

    def test_create_graph_node(self) -> None:
        """Test creating a valid GraphNode."""
        loc = SourceLocation(
            file_path="/path/to/file.py",
            start_byte=0,
            end_byte=100,
            start_line=1,
            start_column=0,
            end_line=5,
            end_column=10,
        )
        node = GraphNode(
            id="abc123",
            type=NodeType.FUNCTION,
            name="my_function",
            qualified_name="module.my_function",
            language="python",
            signature="def my_function(x: int) -> int:",
            location=loc,
        )
        assert node.id == "abc123"
        assert node.type == NodeType.FUNCTION
        assert node.name == "my_function"
        assert node.language == "python"

    def test_node_types(self) -> None:
        """Test all NodeType enum values exist."""
        assert NodeType.MODULE == "module"
        assert NodeType.FUNCTION == "function"
        assert NodeType.CLASS == "class"
        assert NodeType.METHOD == "method"
        assert NodeType.IMPORT == "import"
        assert NodeType.CALL == "call"

    def test_graph_node_json_serialization(self) -> None:
        """Test that GraphNode serializes to JSON correctly."""
        loc = SourceLocation(
            file_path="/path/to/file.py",
            start_byte=0,
            end_byte=100,
            start_line=1,
            start_column=0,
            end_line=5,
            end_column=10,
        )
        node = GraphNode(
            id="abc123",
            type=NodeType.FUNCTION,
            name="my_function",
            qualified_name="module.my_function",
            language="python",
            signature="def my_function(x: int) -> int:",
            location=loc,
        )
        json_str = node.model_dump_json()
        assert '"id":"abc123"' in json_str
        assert '"type":"function"' in json_str


class TestGraphEdge:
    """Tests for GraphEdge model."""

    def test_create_graph_edge(self) -> None:
        """Test creating a valid GraphEdge."""
        edge = GraphEdge(
            source_id="node1",
            target_id="node2",
            type=EdgeType.CALLS,
        )
        assert edge.source_id == "node1"
        assert edge.target_id == "node2"
        assert edge.type == EdgeType.CALLS

    def test_edge_types(self) -> None:
        """Test all EdgeType enum values exist."""
        assert EdgeType.CALLS == "calls"
        assert EdgeType.IMPORTS == "imports"
        assert EdgeType.DEFINES == "defines"
        assert EdgeType.INHERITS == "inherits"
        assert EdgeType.CONTAINS == "contains"


class TestSegment:
    """Tests for Segment model."""

    def test_create_segment(self) -> None:
        """Test creating a valid Segment."""
        segment = Segment(
            minified_start=0,
            minified_end=50,
            original_start=0,
            original_end=100,
        )
        assert segment.minified_start == 0
        assert segment.minified_end == 50
        assert segment.original_start == 0
        assert segment.original_end == 100

    def test_segment_length_properties(self) -> None:
        """Test Segment length calculation properties."""
        segment = Segment(
            minified_start=0,
            minified_end=50,
            original_start=0,
            original_end=100,
        )
        assert segment.minified_length == 50
        assert segment.original_length == 100

    def test_segment_is_frozen(self) -> None:
        """Test that Segment is immutable."""
        segment = Segment(
            minified_start=0,
            minified_end=50,
            original_start=0,
            original_end=100,
        )
        with pytest.raises(ValidationError):
            segment.minified_start = 10  # type: ignore
