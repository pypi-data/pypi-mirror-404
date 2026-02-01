"""Unit tests for the ContextGraph module."""

import pytest

from mcp_context_graph.core.edge import EdgeType, GraphEdge
from mcp_context_graph.core.graph import ContextGraph
from mcp_context_graph.core.node import GraphNode, NodeType, SourceLocation


@pytest.fixture
def sample_location() -> SourceLocation:
    """Create a sample source location for tests."""
    return SourceLocation(
        file_path="test.py",
        start_byte=0,
        end_byte=100,
        start_line=1,
        start_column=0,
        end_line=5,
        end_column=10,
    )


@pytest.fixture
def sample_function_node(sample_location: SourceLocation) -> GraphNode:
    """Create a sample function node for tests."""
    return GraphNode(
        id="func_abc123",
        type=NodeType.FUNCTION,
        name="my_function",
        qualified_name="test.py:my_function",
        language="python",
        signature="def my_function(x: int) -> str:",
        location=sample_location,
        source_map_id="map_123",
    )


@pytest.fixture
def sample_class_node() -> GraphNode:
    """Create a sample class node for tests."""
    return GraphNode(
        id="class_def456",
        type=NodeType.CLASS,
        name="MyClass",
        qualified_name="test.py:MyClass",
        language="python",
        signature="class MyClass:",
        location=SourceLocation(
            file_path="test.py",
            start_byte=100,
            end_byte=200,
            start_line=6,
            start_column=0,
            end_line=20,
            end_column=0,
        ),
        source_map_id="map_456",
    )


@pytest.fixture
def sample_caller_node() -> GraphNode:
    """Create a sample caller function node for tests."""
    return GraphNode(
        id="caller_789",
        type=NodeType.FUNCTION,
        name="caller_func",
        qualified_name="test.py:caller_func",
        language="python",
        signature="def caller_func():",
        location=SourceLocation(
            file_path="test.py",
            start_byte=200,
            end_byte=300,
            start_line=21,
            start_column=0,
            end_line=25,
            end_column=0,
        ),
        source_map_id="map_789",
    )


class TestContextGraphInit:
    """Tests for ContextGraph initialization."""

    def test_init_empty_graph(self):
        """Test creating an empty graph."""
        graph = ContextGraph()
        assert graph.node_count == 0
        assert graph.edge_count == 0
        assert len(graph) == 0
        assert not graph  # bool should be False when empty

    def test_repr(self):
        """Test string representation."""
        graph = ContextGraph()
        assert "ContextGraph" in repr(graph)
        assert "nodes=0" in repr(graph)
        assert "edges=0" in repr(graph)


class TestContextGraphNodes:
    """Tests for node operations."""

    def test_add_node(self, sample_function_node: GraphNode):
        """Test adding a single node."""
        graph = ContextGraph()
        graph.add_node(sample_function_node)

        assert graph.node_count == 1
        assert sample_function_node.id in graph
        assert graph  # bool should be True when not empty

    def test_add_node_duplicate_raises(self, sample_function_node: GraphNode):
        """Test that adding duplicate node ID raises ValueError."""
        graph = ContextGraph()
        graph.add_node(sample_function_node)

        with pytest.raises(ValueError, match="already exists"):
            graph.add_node(sample_function_node)

    def test_get_node(self, sample_function_node: GraphNode):
        """Test retrieving a node by ID."""
        graph = ContextGraph()
        graph.add_node(sample_function_node)

        retrieved = graph.get_node(sample_function_node.id)
        assert retrieved is not None
        assert retrieved.id == sample_function_node.id
        assert retrieved.name == sample_function_node.name

    def test_get_node_not_found(self):
        """Test getting non-existent node returns None."""
        graph = ContextGraph()
        assert graph.get_node("nonexistent") is None

    def test_remove_node(self, sample_function_node: GraphNode):
        """Test removing a node."""
        graph = ContextGraph()
        graph.add_node(sample_function_node)

        result = graph.remove_node(sample_function_node.id)
        assert result is True
        assert graph.node_count == 0
        assert sample_function_node.id not in graph

    def test_remove_node_not_found(self):
        """Test removing non-existent node returns False."""
        graph = ContextGraph()
        result = graph.remove_node("nonexistent")
        assert result is False

    def test_iter_nodes(
        self,
        sample_function_node: GraphNode,
        sample_class_node: GraphNode,
    ):
        """Test iterating over nodes."""
        graph = ContextGraph()
        graph.add_node(sample_function_node)
        graph.add_node(sample_class_node)

        nodes = list(graph.iter_nodes())
        assert len(nodes) == 2

    def test_get_all_nodes(
        self,
        sample_function_node: GraphNode,
        sample_class_node: GraphNode,
    ):
        """Test getting all nodes as a list."""
        graph = ContextGraph()
        graph.add_node(sample_function_node)
        graph.add_node(sample_class_node)

        nodes = graph.get_all_nodes()
        assert len(nodes) == 2
        assert isinstance(nodes, list)


class TestContextGraphEdges:
    """Tests for edge operations."""

    def test_add_edge(
        self,
        sample_function_node: GraphNode,
        sample_caller_node: GraphNode,
    ):
        """Test adding an edge between nodes."""
        graph = ContextGraph()
        graph.add_node(sample_function_node)
        graph.add_node(sample_caller_node)

        edge = GraphEdge(
            source_id=sample_caller_node.id,
            target_id=sample_function_node.id,
            type=EdgeType.CALLS,
        )
        graph.add_edge(edge)

        assert graph.edge_count == 1
        assert graph.has_edge(sample_caller_node.id, sample_function_node.id)

    def test_add_edge_missing_source_raises(self, sample_function_node: GraphNode):
        """Test that adding edge with missing source raises ValueError."""
        graph = ContextGraph()
        graph.add_node(sample_function_node)

        edge = GraphEdge(
            source_id="nonexistent",
            target_id=sample_function_node.id,
            type=EdgeType.CALLS,
        )

        with pytest.raises(ValueError, match="Source node"):
            graph.add_edge(edge)

    def test_add_edge_missing_target_raises(self, sample_function_node: GraphNode):
        """Test that adding edge with missing target raises ValueError."""
        graph = ContextGraph()
        graph.add_node(sample_function_node)

        edge = GraphEdge(
            source_id=sample_function_node.id,
            target_id="nonexistent",
            type=EdgeType.CALLS,
        )

        with pytest.raises(ValueError, match="Target node"):
            graph.add_edge(edge)

    def test_get_edge(
        self,
        sample_function_node: GraphNode,
        sample_caller_node: GraphNode,
    ):
        """Test retrieving an edge."""
        graph = ContextGraph()
        graph.add_node(sample_function_node)
        graph.add_node(sample_caller_node)

        edge = GraphEdge(
            source_id=sample_caller_node.id,
            target_id=sample_function_node.id,
            type=EdgeType.CALLS,
        )
        graph.add_edge(edge)

        retrieved = graph.get_edge(sample_caller_node.id, sample_function_node.id)
        assert retrieved is not None
        assert retrieved.type == EdgeType.CALLS

    def test_get_edge_not_found(self):
        """Test getting non-existent edge returns None."""
        graph = ContextGraph()
        assert graph.get_edge("a", "b") is None

    def test_iter_edges(
        self,
        sample_function_node: GraphNode,
        sample_caller_node: GraphNode,
    ):
        """Test iterating over edges."""
        graph = ContextGraph()
        graph.add_node(sample_function_node)
        graph.add_node(sample_caller_node)

        edge = GraphEdge(
            source_id=sample_caller_node.id,
            target_id=sample_function_node.id,
            type=EdgeType.CALLS,
        )
        graph.add_edge(edge)

        edges = list(graph.iter_edges())
        assert len(edges) == 1
        assert edges[0].type == EdgeType.CALLS


class TestContextGraphQueries:
    """Tests for query methods."""

    def test_find_definition(self, sample_function_node: GraphNode):
        """Test finding a definition by name."""
        graph = ContextGraph()
        graph.add_node(sample_function_node)

        result = graph.find_definition("my_function")
        assert result is not None
        assert result.name == "my_function"

    def test_find_definition_not_found(self):
        """Test finding non-existent definition returns None."""
        graph = ContextGraph()
        result = graph.find_definition("nonexistent")
        assert result is None

    def test_find_definitions_multiple(self, sample_location: SourceLocation):
        """Test finding multiple definitions with same name."""
        graph = ContextGraph()

        node1 = GraphNode(
            id="func_1",
            type=NodeType.FUNCTION,
            name="helper",
            qualified_name="file1.py:helper",
            language="python",
            signature="def helper():",
            location=sample_location,
        )
        node2 = GraphNode(
            id="func_2",
            type=NodeType.FUNCTION,
            name="helper",
            qualified_name="file2.py:helper",
            language="python",
            signature="def helper():",
            location=SourceLocation(
                file_path="file2.py",
                start_byte=0,
                end_byte=50,
                start_line=1,
                start_column=0,
                end_line=3,
                end_column=0,
            ),
        )

        graph.add_node(node1)
        graph.add_node(node2)

        results = graph.find_definitions("helper")
        assert len(results) == 2

    def test_find_by_qualified_name(self, sample_function_node: GraphNode):
        """Test finding by fully qualified name."""
        graph = ContextGraph()
        graph.add_node(sample_function_node)

        result = graph.find_by_qualified_name("test.py:my_function")
        assert result is not None
        assert result.id == sample_function_node.id

    def test_find_by_type(
        self,
        sample_function_node: GraphNode,
        sample_class_node: GraphNode,
    ):
        """Test finding nodes by type."""
        graph = ContextGraph()
        graph.add_node(sample_function_node)
        graph.add_node(sample_class_node)

        functions = graph.find_by_type(NodeType.FUNCTION)
        assert len(functions) == 1
        assert functions[0].type == NodeType.FUNCTION

        classes = graph.find_by_type(NodeType.CLASS)
        assert len(classes) == 1
        assert classes[0].type == NodeType.CLASS

    def test_find_by_file(
        self,
        sample_function_node: GraphNode,
        sample_class_node: GraphNode,
    ):
        """Test finding nodes by file path."""
        graph = ContextGraph()
        graph.add_node(sample_function_node)
        graph.add_node(sample_class_node)

        results = graph.find_by_file("test.py")
        assert len(results) == 2

    def test_find_callers(
        self,
        sample_function_node: GraphNode,
        sample_caller_node: GraphNode,
    ):
        """Test finding callers of a function."""
        graph = ContextGraph()
        graph.add_node(sample_function_node)
        graph.add_node(sample_caller_node)

        edge = GraphEdge(
            source_id=sample_caller_node.id,
            target_id=sample_function_node.id,
            type=EdgeType.CALLS,
        )
        graph.add_edge(edge)

        callers = graph.find_callers("my_function")
        assert len(callers) == 1
        assert callers[0].name == "caller_func"

    def test_find_callers_not_found(self):
        """Test finding callers of non-existent function."""
        graph = ContextGraph()
        callers = graph.find_callers("nonexistent")
        assert callers == []

    def test_find_callees(
        self,
        sample_function_node: GraphNode,
        sample_caller_node: GraphNode,
    ):
        """Test finding callees of a function."""
        graph = ContextGraph()
        graph.add_node(sample_function_node)
        graph.add_node(sample_caller_node)

        edge = GraphEdge(
            source_id=sample_caller_node.id,
            target_id=sample_function_node.id,
            type=EdgeType.CALLS,
        )
        graph.add_edge(edge)

        callees = graph.find_callees("caller_func")
        assert len(callees) == 1
        assert callees[0].name == "my_function"

    def test_find_imports(self, sample_location: SourceLocation):
        """Test finding imports."""
        graph = ContextGraph()

        import_node = GraphNode(
            id="import_123",
            type=NodeType.IMPORT,
            name="os",
            qualified_name="test.py:import:os",
            language="python",
            signature="import os",
            location=sample_location,
        )
        graph.add_node(import_node)

        imports = graph.find_imports("os")
        assert len(imports) == 1
        assert imports[0].type == NodeType.IMPORT

    def test_get_context_subgraph(
        self,
        sample_function_node: GraphNode,
        sample_caller_node: GraphNode,
    ):
        """Test getting context subgraph around a node."""
        graph = ContextGraph()
        graph.add_node(sample_function_node)
        graph.add_node(sample_caller_node)

        edge = GraphEdge(
            source_id=sample_caller_node.id,
            target_id=sample_function_node.id,
            type=EdgeType.CALLS,
        )
        graph.add_edge(edge)

        context = graph.get_context_subgraph("my_function", depth=1)
        assert len(context) == 2  # The node and its caller

    def test_get_context_subgraph_depth_0(self, sample_function_node: GraphNode):
        """Test context subgraph with depth 0 returns only the node."""
        graph = ContextGraph()
        graph.add_node(sample_function_node)

        context = graph.get_context_subgraph("my_function", depth=0)
        assert len(context) == 1


class TestContextGraphVisualization:
    """Tests for visualization methods."""

    def test_to_mermaid(
        self,
        sample_function_node: GraphNode,
        sample_caller_node: GraphNode,
    ):
        """Test Mermaid diagram generation."""
        graph = ContextGraph()
        graph.add_node(sample_function_node)
        graph.add_node(sample_caller_node)

        edge = GraphEdge(
            source_id=sample_caller_node.id,
            target_id=sample_function_node.id,
            type=EdgeType.CALLS,
        )
        graph.add_edge(edge)

        mermaid = graph.to_mermaid()
        assert "graph LR" in mermaid
        assert "my_function" in mermaid
        assert "caller_func" in mermaid
        assert "CALLS" in mermaid

    def test_to_mermaid_max_nodes(self, sample_location: SourceLocation):
        """Test Mermaid with max_nodes limit."""
        graph = ContextGraph()

        # Add more nodes than the limit
        for i in range(10):
            node = GraphNode(
                id=f"func_{i}",
                type=NodeType.FUNCTION,
                name=f"func_{i}",
                qualified_name=f"test.py:func_{i}",
                language="python",
                signature=f"def func_{i}():",
                location=sample_location,
            )
            graph.add_node(node)

        mermaid = graph.to_mermaid(max_nodes=5)
        assert "Showing 5 of 10" in mermaid

    def test_to_json(self, sample_function_node: GraphNode):
        """Test JSON export."""
        graph = ContextGraph()
        graph.add_node(sample_function_node)

        import json

        json_str = graph.to_json()
        data = json.loads(json_str)

        assert "nodes" in data
        assert "edges" in data
        assert "stats" in data
        assert len(data["nodes"]) == 1

    def test_to_dot(
        self,
        sample_function_node: GraphNode,
        sample_caller_node: GraphNode,
    ):
        """Test DOT format export."""
        graph = ContextGraph()
        graph.add_node(sample_function_node)
        graph.add_node(sample_caller_node)

        edge = GraphEdge(
            source_id=sample_caller_node.id,
            target_id=sample_function_node.id,
            type=EdgeType.CALLS,
        )
        graph.add_edge(edge)

        dot = graph.to_dot()
        assert "digraph" in dot
        assert "my_function" in dot
        assert "caller_func" in dot


class TestContextGraphRemoveByFile:
    """Tests for file-based node removal (lazy re-ingestion support)."""

    def test_remove_nodes_by_file_single_file(self):
        """Test removing all nodes from a single file."""
        graph = ContextGraph()

        # Add nodes from two different files
        node1 = GraphNode(
            id="func_1",
            type=NodeType.FUNCTION,
            name="func_one",
            qualified_name="file1.py:func_one",
            language="python",
            signature="def func_one():",
            location=SourceLocation(
                file_path="file1.py",
                start_byte=0,
                end_byte=50,
                start_line=1,
                start_column=0,
                end_line=3,
                end_column=0,
            ),
        )
        node2 = GraphNode(
            id="func_2",
            type=NodeType.FUNCTION,
            name="func_two",
            qualified_name="file1.py:func_two",
            language="python",
            signature="def func_two():",
            location=SourceLocation(
                file_path="file1.py",
                start_byte=50,
                end_byte=100,
                start_line=4,
                start_column=0,
                end_line=6,
                end_column=0,
            ),
        )
        node3 = GraphNode(
            id="func_3",
            type=NodeType.FUNCTION,
            name="func_three",
            qualified_name="file2.py:func_three",
            language="python",
            signature="def func_three():",
            location=SourceLocation(
                file_path="file2.py",
                start_byte=0,
                end_byte=50,
                start_line=1,
                start_column=0,
                end_line=3,
                end_column=0,
            ),
        )

        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_node(node3)

        assert graph.node_count == 3

        # Remove nodes from file1.py
        removed = graph.remove_nodes_by_file("file1.py")

        assert removed == 2
        assert graph.node_count == 1
        assert graph.get_node("func_1") is None
        assert graph.get_node("func_2") is None
        assert graph.get_node("func_3") is not None

    def test_remove_nodes_by_file_with_edges(self):
        """Test that removing nodes also removes incident edges."""
        graph = ContextGraph()

        node1 = GraphNode(
            id="module_1",
            type=NodeType.MODULE,
            name="module1",
            qualified_name="file1.py",
            language="python",
            signature="# file1.py",
            location=SourceLocation(
                file_path="file1.py",
                start_byte=0,
                end_byte=100,
                start_line=1,
                start_column=0,
                end_line=10,
                end_column=0,
            ),
        )
        node2 = GraphNode(
            id="func_1",
            type=NodeType.FUNCTION,
            name="func_one",
            qualified_name="file1.py:func_one",
            language="python",
            signature="def func_one():",
            location=SourceLocation(
                file_path="file1.py",
                start_byte=10,
                end_byte=50,
                start_line=2,
                start_column=0,
                end_line=4,
                end_column=0,
            ),
        )

        graph.add_node(node1)
        graph.add_node(node2)

        # Add edge
        edge = GraphEdge(
            source_id="module_1",
            target_id="func_1",
            type=EdgeType.CONTAINS,
        )
        graph.add_edge(edge)

        assert graph.edge_count == 1

        # Remove by file - should remove both nodes and the edge
        removed = graph.remove_nodes_by_file("file1.py")

        assert removed == 2
        assert graph.node_count == 0
        assert graph.edge_count == 0

    def test_remove_nodes_by_file_not_found(self):
        """Test removing nodes from non-existent file returns 0."""
        graph = ContextGraph()
        removed = graph.remove_nodes_by_file("nonexistent.py")
        assert removed == 0

    def test_remove_nodes_by_file_updates_indices(self):
        """Test that indices are properly updated after removal."""
        graph = ContextGraph()

        node = GraphNode(
            id="func_1",
            type=NodeType.FUNCTION,
            name="my_func",
            qualified_name="file1.py:my_func",
            language="python",
            signature="def my_func():",
            location=SourceLocation(
                file_path="file1.py",
                start_byte=0,
                end_byte=50,
                start_line=1,
                start_column=0,
                end_line=3,
                end_column=0,
            ),
        )
        graph.add_node(node)

        # Verify node is findable
        assert graph.find_definition("my_func") is not None
        assert graph.find_by_file("file1.py") != []

        # Remove by file
        graph.remove_nodes_by_file("file1.py")

        # Verify indices are cleared
        assert graph.find_definition("my_func") is None
        assert graph.find_by_file("file1.py") == []
        assert graph.find_by_qualified_name("file1.py:my_func") is None


class TestContextGraphClear:
    """Tests for graph clearing."""

    def test_clear(
        self,
        sample_function_node: GraphNode,
        sample_caller_node: GraphNode,
    ):
        """Test clearing all nodes and edges."""
        graph = ContextGraph()
        graph.add_node(sample_function_node)
        graph.add_node(sample_caller_node)

        edge = GraphEdge(
            source_id=sample_caller_node.id,
            target_id=sample_function_node.id,
            type=EdgeType.CALLS,
        )
        graph.add_edge(edge)

        graph.clear()

        assert graph.node_count == 0
        assert graph.edge_count == 0
        assert not graph
