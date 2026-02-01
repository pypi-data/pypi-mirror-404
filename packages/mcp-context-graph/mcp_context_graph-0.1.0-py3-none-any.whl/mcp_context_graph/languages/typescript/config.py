"""
TypeScriptConfig and JavaScriptConfig: TypeScript/JavaScript language configurations.

Contains:
- Tree-sitter TypeScript/JavaScript grammar loading
- Paths to .scm query files
- TypeScript/JavaScript-specific node type mappings
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from mcp_context_graph.languages.base import LanguageConfig

if TYPE_CHECKING:
    from tree_sitter import Language

logger = logging.getLogger(__name__)


class TypeScriptConfig(LanguageConfig):
    """
    TypeScript-specific language configuration.

    Provides tree-sitter grammar and queries for parsing TypeScript files.
    Supports .ts and .tsx extensions.
    """

    @property
    def name(self) -> str:
        """Return the canonical language name."""
        return "typescript"

    @property
    def file_extensions(self) -> tuple[str, ...]:
        """Return supported file extensions."""
        return (".ts", ".tsx")

    def _default_queries_dir(self) -> Path:
        """Return the default path to the queries directory."""
        return Path(__file__).parent / "queries"

    def _load_language(self) -> Language:
        """Load the tree-sitter TypeScript language."""
        import tree_sitter_typescript as ts_typescript

        # tree-sitter-typescript provides separate languages for TS and TSX
        # We use the TypeScript language for both (TSX is a superset)
        return ts_typescript.language_typescript()  # type: ignore[return-value]

    # -------------------------------------------------------------------------
    # TypeScript-specific node type mappings
    # -------------------------------------------------------------------------

    @property
    def function_node_types(self) -> tuple[str, ...]:
        """TypeScript function definition node types."""
        return (
            "function_declaration",
            "method_definition",
            "arrow_function",
            "function_expression",
        )

    @property
    def class_node_types(self) -> tuple[str, ...]:
        """TypeScript class definition node types."""
        return ("class_declaration",)

    @property
    def call_node_types(self) -> tuple[str, ...]:
        """TypeScript function call node types."""
        return ("call_expression",)

    @property
    def import_node_types(self) -> tuple[str, ...]:
        """TypeScript import statement node types."""
        return ("import_statement",)

    @property
    def body_node_type(self) -> str:
        """TypeScript uses 'statement_block' for function bodies."""
        return "statement_block"

    # -------------------------------------------------------------------------
    # TypeScript-specific helpers
    # -------------------------------------------------------------------------

    @property
    def interface_node_types(self) -> tuple[str, ...]:
        """TypeScript interface declaration node types."""
        return ("interface_declaration",)

    @property
    def type_alias_node_types(self) -> tuple[str, ...]:
        """TypeScript type alias declaration node types."""
        return ("type_alias_declaration",)

    @property
    def export_node_types(self) -> tuple[str, ...]:
        """TypeScript export statement node types."""
        return ("export_statement",)


class JavaScriptConfig(LanguageConfig):
    """
    JavaScript-specific language configuration.

    Provides tree-sitter grammar and queries for parsing JavaScript files.
    Supports .js, .jsx, .mjs, and .cjs extensions.

    Note: JavaScript uses the same queries as TypeScript for simplicity.
    """

    @property
    def name(self) -> str:
        """Return the canonical language name."""
        return "javascript"

    @property
    def file_extensions(self) -> tuple[str, ...]:
        """Return supported file extensions."""
        return (".js", ".jsx", ".mjs", ".cjs")

    def _default_queries_dir(self) -> Path:
        """Return the default path to the queries directory.

        JavaScript shares queries with TypeScript since they're similar.
        """
        return Path(__file__).parent / "queries"

    def _load_language(self) -> Language:
        """Load the tree-sitter JavaScript language."""
        import tree_sitter_javascript as ts_javascript

        return ts_javascript.language()  # type: ignore[return-value]

    # -------------------------------------------------------------------------
    # JavaScript-specific node type mappings
    # -------------------------------------------------------------------------

    @property
    def function_node_types(self) -> tuple[str, ...]:
        """JavaScript function definition node types."""
        return (
            "function_declaration",
            "method_definition",
            "arrow_function",
            "function_expression",
            "generator_function_declaration",
        )

    @property
    def class_node_types(self) -> tuple[str, ...]:
        """JavaScript class definition node types."""
        return ("class_declaration",)

    @property
    def call_node_types(self) -> tuple[str, ...]:
        """JavaScript function call node types."""
        return ("call_expression",)

    @property
    def import_node_types(self) -> tuple[str, ...]:
        """JavaScript import statement node types."""
        return ("import_statement",)

    @property
    def body_node_type(self) -> str:
        """JavaScript uses 'statement_block' for function bodies."""
        return "statement_block"

    # -------------------------------------------------------------------------
    # JavaScript-specific helpers
    # -------------------------------------------------------------------------

    @property
    def export_node_types(self) -> tuple[str, ...]:
        """JavaScript export statement node types."""
        return ("export_statement",)

    @property
    def require_call_types(self) -> tuple[str, ...]:
        """CommonJS require() call pattern."""
        return ("call_expression",)  # Needs additional analysis for 'require'
