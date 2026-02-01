"""Tests to ensure all modules can be imported (100% coverage of __init__.py files)."""


def test_import_mcp_context_graph() -> None:
    """Test importing the main package."""
    import mcp_context_graph

    assert mcp_context_graph.__version__ == "0.1.0"
    assert mcp_context_graph.logger is not None


def test_import_core() -> None:
    """Test importing core module."""
    from mcp_context_graph import core

    assert core.NodeType is not None
    assert core.GraphNode is not None
    assert core.EdgeType is not None
    assert core.GraphEdge is not None


def test_import_ingest() -> None:
    """Test importing ingest module."""
    from mcp_context_graph import ingest

    assert "Minifier" in ingest.__all__
    assert "MinificationResult" in ingest.__all__
    assert ingest.Minifier is not None


def test_import_languages() -> None:
    """Test importing languages module."""
    from mcp_context_graph import languages

    assert "LanguageConfig" in languages.__all__
    assert "LanguageRegistry" in languages.__all__
    assert "get_registry" in languages.__all__
    assert "get_language_for_file" in languages.__all__
    assert languages.LanguageConfig is not None
    assert languages.LanguageRegistry is not None


def test_import_languages_python() -> None:
    """Test importing python language module."""
    from mcp_context_graph.languages import python

    assert "PythonConfig" in python.__all__
    assert python.PythonConfig is not None


def test_import_languages_typescript() -> None:
    """Test importing typescript language module."""
    from mcp_context_graph.languages import typescript

    assert "TypeScriptConfig" in typescript.__all__
    assert "JavaScriptConfig" in typescript.__all__
    assert typescript.TypeScriptConfig is not None
    assert typescript.JavaScriptConfig is not None


def test_import_provenance() -> None:
    """Test importing provenance module."""
    from mcp_context_graph import provenance

    assert "Segment" in provenance.__all__
    assert "SourceMap" in provenance.__all__
    assert provenance.Segment is not None
    assert provenance.SourceMap is not None


def test_import_mcp() -> None:
    """Test importing mcp module."""
    from mcp_context_graph import mcp

    # MCP module now exports server and tools
    assert "MCPContextGraphServer" in mcp.__all__
    assert "run_server" in mcp.__all__
    assert "IndexProjectInput" in mcp.__all__
    assert "FindSymbolInput" in mcp.__all__
    assert "FindCallersInput" in mcp.__all__
    assert "GetContextInput" in mcp.__all__
    assert "ExpandSourceInput" in mcp.__all__
    assert "DebugDumpGraphInput" in mcp.__all__
    assert mcp.MCPContextGraphServer is not None
    assert mcp.run_server is not None
