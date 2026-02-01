"""
Ingest module: Polyglot parsing and ingestion.

This module provides the ingestion pipeline components:
- Ingestor: Orchestrator for file ingestion
- TreeSitterParser: Tree-sitter wrapper for parsing
- Normalizer: AST normalization to generic nodes
- Minifier: Signature extraction with source maps
"""

from mcp_context_graph.ingest.ingestor import (
    Ingestor,
    IngestorStats,
    ProvenanceTracker,
)
from mcp_context_graph.ingest.minifier import (
    BODY_PLACEHOLDER,
    MinificationResult,
    Minifier,
    create_identity_minification,
)
from mcp_context_graph.ingest.normalizer import (
    GenericNode,
    NormalizationResult,
    Normalizer,
)
from mcp_context_graph.ingest.tree_sitter_parser import (
    ParsedCapture,
    ParseResult,
    TreeSitterParser,
)

__all__ = [
    # Ingestor
    "Ingestor",
    "IngestorStats",
    "ProvenanceTracker",
    # Parser
    "TreeSitterParser",
    "ParseResult",
    "ParsedCapture",
    # Normalizer
    "Normalizer",
    "NormalizationResult",
    "GenericNode",
    # Minifier
    "Minifier",
    "MinificationResult",
    "BODY_PLACEHOLDER",
    "create_identity_minification",
]
