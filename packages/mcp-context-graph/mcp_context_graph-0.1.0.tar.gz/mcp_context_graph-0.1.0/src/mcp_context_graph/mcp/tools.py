"""
Tool definitions for MCP.

Defines the tools exposed by the MCP server:
- index_project: Full scan of project directory
- find_symbol: Find definitions by name
- find_callers: Who calls this function?
- get_context: Context window around a symbol
- expand_source: De-minify a node using source maps
- debug_dump_graph: Mermaid/JSON/DOT visualization

CRITICAL: Every field has a description="..." for MCP Inspector UI.
CRITICAL: Every tool execution starts with ingestor.refresh_if_needed().
CRITICAL: NO print() statements - use logger only.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from pathlib import Path

    from mcp_context_graph.ingest.ingestor import Ingestor

logger = logging.getLogger(__name__)


# =============================================================================
# Input Models with MCP Inspector-friendly descriptions
# =============================================================================


class IndexProjectInput(BaseModel):
    """Input model for index_project tool."""

    path: str | None = Field(
        default=None,
        description=(
            "Path to the project directory to index. "
            "If not provided, uses the project root configured at server startup. "
            "Example: '/path/to/my-project'"
        ),
    )
    force: bool = Field(
        default=False,
        description=(
            "Force full re-indexing even if files haven't changed. "
            "Set to true to rebuild the entire graph from scratch."
        ),
    )


class FindSymbolInput(BaseModel):
    """Input model for find_symbol tool."""

    name: str = Field(
        description=(
            "The symbol name to search for (e.g., 'calculate_tax', 'MyClass'). "
            "Searches function, class, and method definitions."
        ),
    )
    language: str | None = Field(
        default=None,
        description=(
            "Filter results to specific language (e.g., 'python', 'typescript', 'javascript'). "
            "Leave empty to search all languages."
        ),
    )
    include_calls: bool = Field(
        default=False,
        description=(
            "Include all call sites where this symbol is used. "
            "When true, returns both definitions and call locations."
        ),
    )


class FindCallersInput(BaseModel):
    """Input model for find_callers tool."""

    name: str = Field(
        description=(
            "The function or method name to find callers for. "
            "Returns all locations in the codebase that call this function."
        ),
    )


class GetContextInput(BaseModel):
    """Input model for get_context tool."""

    symbol_id: str | None = Field(
        default=None,
        description=(
            "The unique ID of the symbol (returned from find_symbol). "
            "Use either symbol_id or name, not both."
        ),
    )
    name: str | None = Field(
        default=None,
        description=(
            "The symbol name to get context for. "
            "Use either symbol_id or name, not both."
        ),
    )
    depth: int = Field(
        default=1,
        ge=0,
        le=5,
        description=(
            "Context depth: 0=just the node, 1=direct callers/callees, "
            "2=indirect connections, etc. Maximum depth is 5."
        ),
    )
    format: str = Field(
        default="json",
        description=(
            "Response format: 'json' for structured data suitable for parsing, "
            "'markdown' for human-readable text with code blocks."
        ),
    )


class ExpandSourceInput(BaseModel):
    """Input model for expand_source tool."""

    symbol_id: str | None = Field(
        default=None,
        description=(
            "The unique ID of the symbol to expand. "
            "Use either symbol_id or name, not both."
        ),
    )
    name: str | None = Field(
        default=None,
        description=(
            "The symbol name to expand. " "Use either symbol_id or name, not both."
        ),
    )
    start_offset: int | None = Field(
        default=None,
        description=(
            "Starting byte offset in minified text (optional). "
            "If not provided, expands the full original source."
        ),
    )
    end_offset: int | None = Field(
        default=None,
        description=(
            "Ending byte offset in minified text (optional). "
            "If not provided, expands to the end of the symbol."
        ),
    )


class DebugDumpGraphInput(BaseModel):
    """Input for debug_dump_graph tool."""

    format: str = Field(
        default="mermaid",
        description=(
            "Output format: 'mermaid' for Mermaid flowchart diagram, "
            "'json' for raw structure with all node/edge data, "
            "'dot' for Graphviz DOT format."
        ),
    )
    limit_nodes: int | None = Field(
        default=50,
        description=(
            "Maximum nodes to include in output (for large graphs). "
            "Set to null/None to include all nodes."
        ),
    )
    show_edges: bool = Field(
        default=True,
        description="Include edge relationships in output.",
    )


# =============================================================================
# Tool Logic Functions
# =============================================================================


def refresh_graph(ingestor: Ingestor) -> list[str]:
    """
    Ensure graph is fresh before querying.

    This is the lazy ingestion hook - checks for changed files
    and re-ingests them before any query operation.

    Args:
        ingestor: The Ingestor instance to refresh.

    Returns:
        List of files that were refreshed.
    """
    refreshed = ingestor.refresh_changed_files()
    if refreshed:
        logger.info("Refreshed %d files before query: %s", len(refreshed), refreshed)
    return refreshed


def tool_index_project(
    params: IndexProjectInput,
    ingestor: Ingestor,
    project_root: Path,
) -> dict[str, Any]:
    """
    Execute index_project tool - full scan of project directory.

    Args:
        params: Input parameters.
        ingestor: The Ingestor instance.
        project_root: Default project root path.

    Returns:
        Dictionary with indexing results.
    """
    logger.info("index_project called with params: %s", params)

    # Determine the path to index
    if params.path:
        from pathlib import Path as PathLib

        target_path = PathLib(params.path).resolve()
    else:
        target_path = project_root

    # If force=True, clear the graph and re-ingest
    if params.force:
        logger.info("Force flag set - clearing graph and re-indexing")
        ingestor.graph.clear()
        ingestor.tracker.clear()

    # Run ingestion
    graph, tracker, stats = ingestor.ingest()

    return {
        "success": True,
        "project_path": str(target_path),
        "stats": {
            "files_discovered": stats.files_discovered,
            "files_processed": stats.files_processed,
            "files_skipped": stats.files_skipped,
            "files_failed": stats.files_failed,
            "nodes_created": stats.nodes_created,
            "edges_created": stats.edges_created,
        },
        "graph_summary": {
            "total_nodes": graph.node_count,
            "total_edges": graph.edge_count,
        },
    }


def tool_find_symbol(
    params: FindSymbolInput,
    ingestor: Ingestor,
) -> dict[str, Any]:
    """
    Execute find_symbol tool - find definitions by name.

    Args:
        params: Input parameters.
        ingestor: The Ingestor instance.

    Returns:
        Dictionary with found symbols.
    """
    logger.info("find_symbol called with params: %s", params)

    # Ensure graph is fresh before querying
    refresh_graph(ingestor)

    graph = ingestor.graph

    # Find all definitions matching the name
    definitions = graph.find_definitions(params.name)

    # Filter by language if specified
    if params.language:
        definitions = [d for d in definitions if d.language == params.language]

    if not definitions:
        return {
            "success": True,
            "found": False,
            "message": f"No definitions found for symbol '{params.name}'",
            "symbols": [],
        }

    # Build result list
    symbols = []
    for node in definitions:
        symbol_data = {
            "id": node.id,
            "name": node.name,
            "type": node.type.value,
            "qualified_name": node.qualified_name,
            "language": node.language,
            "signature": node.signature,
            "location": {
                "file": node.location.file_path,
                "line": node.location.start_line,
                "column": node.location.start_column,
            },
        }
        symbols.append(symbol_data)

    # Optionally include call sites
    call_sites = []
    if params.include_calls:
        for defn in definitions:
            callers = graph.find_callers(defn.name)
            for caller in callers:
                call_sites.append(
                    {
                        "caller_id": caller.id,
                        "caller_name": caller.name,
                        "caller_file": caller.location.file_path,
                        "caller_line": caller.location.start_line,
                    }
                )

    result: dict[str, Any] = {
        "success": True,
        "found": True,
        "count": len(symbols),
        "symbols": symbols,
    }

    if params.include_calls:
        result["call_sites"] = call_sites
        result["call_count"] = len(call_sites)

    return result


def tool_find_callers(
    params: FindCallersInput,
    ingestor: Ingestor,
) -> dict[str, Any]:
    """
    Execute find_callers tool - who calls this function?

    Args:
        params: Input parameters.
        ingestor: The Ingestor instance.

    Returns:
        Dictionary with caller information.
    """
    logger.info("find_callers called with params: %s", params)

    # Ensure graph is fresh before querying
    refresh_graph(ingestor)

    graph = ingestor.graph

    # First find the definition
    definition = graph.find_definition(params.name)
    if not definition:
        return {
            "success": True,
            "found": False,
            "message": f"No definition found for '{params.name}'",
            "callers": [],
        }

    # Find all callers
    callers = graph.find_callers(params.name)

    caller_list = []
    for caller in callers:
        caller_list.append(
            {
                "id": caller.id,
                "name": caller.name,
                "type": caller.type.value,
                "qualified_name": caller.qualified_name,
                "file": caller.location.file_path,
                "line": caller.location.start_line,
                "signature": caller.signature,
            }
        )

    return {
        "success": True,
        "found": True,
        "target": {
            "id": definition.id,
            "name": definition.name,
            "type": definition.type.value,
            "file": definition.location.file_path,
        },
        "caller_count": len(caller_list),
        "callers": caller_list,
    }


def tool_get_context(
    params: GetContextInput,
    ingestor: Ingestor,
) -> dict[str, Any]:
    """
    Execute get_context tool - context window around a symbol.

    Args:
        params: Input parameters.
        ingestor: The Ingestor instance.

    Returns:
        Dictionary with context information.
    """
    logger.info("get_context called with params: %s", params)

    # Ensure graph is fresh before querying
    refresh_graph(ingestor)

    graph = ingestor.graph

    # Determine which symbol to look up
    if params.symbol_id:
        node = graph.get_node(params.symbol_id)
        if not node:
            return {
                "success": False,
                "error": f"No node found with ID '{params.symbol_id}'",
            }
        name = node.name
    elif params.name:
        name = params.name
        node = graph.find_definition(name)
        if not node:
            return {
                "success": False,
                "error": f"No definition found for '{params.name}'",
            }
    else:
        return {
            "success": False,
            "error": "Either 'symbol_id' or 'name' must be provided",
        }

    # Get context subgraph
    context_nodes = graph.get_context_subgraph(name, depth=params.depth)

    if params.format == "markdown":
        # Build markdown representation
        lines = [
            f"# Context for `{name}`",
            "",
            f"**Depth:** {params.depth}",
            f"**Nodes in context:** {len(context_nodes)}",
            "",
            "## Nodes",
            "",
        ]

        for ctx_node in context_nodes:
            is_center = ctx_node.id == node.id
            marker = " ⭐" if is_center else ""
            lines.append(f"### {ctx_node.name}{marker}")
            lines.append(f"- **Type:** {ctx_node.type.value}")
            lines.append(f"- **File:** `{ctx_node.location.file_path}`")
            lines.append(f"- **Line:** {ctx_node.location.start_line}")
            lines.append("```")
            lines.append(ctx_node.signature)
            lines.append("```")
            lines.append("")

        return {
            "success": True,
            "format": "markdown",
            "content": "\n".join(lines),
        }
    else:
        # JSON format
        nodes_data = []
        for ctx_node in context_nodes:
            nodes_data.append(
                {
                    "id": ctx_node.id,
                    "name": ctx_node.name,
                    "type": ctx_node.type.value,
                    "qualified_name": ctx_node.qualified_name,
                    "language": ctx_node.language,
                    "signature": ctx_node.signature,
                    "file": ctx_node.location.file_path,
                    "line": ctx_node.location.start_line,
                    "is_center": ctx_node.id == node.id,
                }
            )

        return {
            "success": True,
            "format": "json",
            "center_node": node.id,
            "depth": params.depth,
            "node_count": len(nodes_data),
            "nodes": nodes_data,
        }


def tool_expand_source(
    params: ExpandSourceInput,
    ingestor: Ingestor,
) -> dict[str, Any]:
    """
    Execute expand_source tool - de-minify a node using source maps.

    Args:
        params: Input parameters.
        ingestor: The Ingestor instance.

    Returns:
        Dictionary with expanded source information.
    """
    logger.info("expand_source called with params: %s", params)

    # Ensure graph is fresh before querying
    refresh_graph(ingestor)

    graph = ingestor.graph
    tracker = ingestor.tracker

    # Determine which symbol to look up
    if params.symbol_id:
        node = graph.get_node(params.symbol_id)
        if not node:
            return {
                "success": False,
                "error": f"No node found with ID '{params.symbol_id}'",
            }
    elif params.name:
        node = graph.find_definition(params.name)
        if not node:
            return {
                "success": False,
                "error": f"No definition found for '{params.name}'",
            }
    else:
        return {
            "success": False,
            "error": "Either 'symbol_id' or 'name' must be provided",
        }

    # Check if node has a source map
    if not node.source_map_id:
        return {
            "success": True,
            "has_source_map": False,
            "message": "Node does not have a source map",
            "signature": node.signature,
        }

    # Get the source map
    source_map = tracker.get(node.source_map_id)
    if not source_map:
        return {
            "success": False,
            "error": f"Source map '{node.source_map_id}' not found in tracker",
        }

    # Determine offsets to map
    start = params.start_offset if params.start_offset is not None else 0
    end = (
        params.end_offset
        if params.end_offset is not None
        else len(node.signature.encode("utf-8"))
    )

    # Map minified offsets to original
    original_start = source_map.minified_to_original(start)
    original_end = source_map.minified_to_original(end)

    # Try to read the original file content
    original_content = None
    try:
        file_path = ingestor.project_root / node.location.file_path
        if file_path.exists():
            full_content = file_path.read_text(encoding="utf-8")
            if original_start is not None and original_end is not None:
                # Extract the relevant portion
                content_bytes = full_content.encode("utf-8")
                original_content = content_bytes[original_start:original_end].decode(
                    "utf-8", errors="replace"
                )
    except Exception as e:
        logger.warning("Failed to read original file: %s", e)

    return {
        "success": True,
        "has_source_map": True,
        "node": {
            "id": node.id,
            "name": node.name,
            "signature": node.signature,
            "file": node.location.file_path,
        },
        "mapping": {
            "minified_start": start,
            "minified_end": end,
            "original_start": original_start,
            "original_end": original_end,
        },
        "original_content": original_content,
    }


def tool_debug_dump_graph(
    params: DebugDumpGraphInput,
    ingestor: Ingestor,
) -> dict[str, Any]:
    """
    Execute debug_dump_graph tool - visualization for debugging.

    Args:
        params: Input parameters.
        ingestor: The Ingestor instance.

    Returns:
        Dictionary with graph visualization.
    """
    logger.info("debug_dump_graph called with params: %s", params)

    # Ensure graph is fresh before querying
    refresh_graph(ingestor)

    graph = ingestor.graph

    if params.format == "mermaid":
        content = graph.to_mermaid(
            max_nodes=params.limit_nodes,
            include_edges=params.show_edges,
        )
        return {
            "success": True,
            "format": "mermaid",
            "content": content,
            "stats": {
                "total_nodes": graph.node_count,
                "total_edges": graph.edge_count,
            },
        }
    elif params.format == "json":
        content = graph.to_json(
            max_nodes=params.limit_nodes,
            include_edges=params.show_edges,
        )
        return {
            "success": True,
            "format": "json",
            "content": content,
            "stats": {
                "total_nodes": graph.node_count,
                "total_edges": graph.edge_count,
            },
        }
    elif params.format == "dot":
        content = graph.to_dot(
            max_nodes=params.limit_nodes,
            include_edges=params.show_edges,
        )
        return {
            "success": True,
            "format": "dot",
            "content": content,
            "stats": {
                "total_nodes": graph.node_count,
                "total_edges": graph.edge_count,
            },
        }
    else:
        return {
            "success": False,
            "error": f"Unknown format: '{params.format}'. Use 'mermaid', 'json', or 'dot'.",
        }
