"""
MCP Server implementation module.

Contains:
- MCPContextGraphServer: Main MCP server wrapper
- run_server: Async entry point for starting the server
- Tool Input Models: Pydantic models for tool inputs
- Tool Functions: Implementation of MCP tools
"""

from mcp_context_graph.mcp.server import MCPContextGraphServer, run_server
from mcp_context_graph.mcp.tools import (
    DebugDumpGraphInput,
    ExpandSourceInput,
    FindCallersInput,
    FindSymbolInput,
    GetContextInput,
    IndexProjectInput,
    tool_debug_dump_graph,
    tool_expand_source,
    tool_find_callers,
    tool_find_symbol,
    tool_get_context,
    tool_index_project,
)

__all__ = [
    # Server
    "MCPContextGraphServer",
    "run_server",
    # Input Models
    "IndexProjectInput",
    "FindSymbolInput",
    "FindCallersInput",
    "GetContextInput",
    "ExpandSourceInput",
    "DebugDumpGraphInput",
    # Tool Functions
    "tool_index_project",
    "tool_find_symbol",
    "tool_find_callers",
    "tool_get_context",
    "tool_expand_source",
    "tool_debug_dump_graph",
]
