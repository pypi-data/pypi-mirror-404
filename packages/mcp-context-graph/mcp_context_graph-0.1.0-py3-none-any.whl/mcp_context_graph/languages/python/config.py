"""
PythonConfig: Python-specific language configuration.

Contains:
- Tree-sitter Python grammar loading
- Paths to .scm query files
- Python-specific node type mappings
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from mcp_context_graph.languages.base import LanguageConfig

if TYPE_CHECKING:
    from tree_sitter import Language

logger = logging.getLogger(__name__)


class PythonConfig(LanguageConfig):
    """
    Python-specific language configuration.

    Provides tree-sitter grammar and queries for parsing Python files.
    Supports .py and .pyw extensions.
    """

    @property
    def name(self) -> str:
        """Return the canonical language name."""
        return "python"

    @property
    def file_extensions(self) -> tuple[str, ...]:
        """Return supported file extensions."""
        return (".py", ".pyw")

    def _default_queries_dir(self) -> Path:
        """Return the default path to the queries directory."""
        return Path(__file__).parent / "queries"

    def _load_language(self) -> Language:
        """Load the tree-sitter Python language."""
        import tree_sitter_python as ts_python

        return ts_python.language()  # type: ignore[return-value]

    # -------------------------------------------------------------------------
    # Python-specific node type mappings
    # -------------------------------------------------------------------------

    @property
    def function_node_types(self) -> tuple[str, ...]:
        """Python function definition node types."""
        return ("function_definition",)

    @property
    def class_node_types(self) -> tuple[str, ...]:
        """Python class definition node types."""
        return ("class_definition",)

    @property
    def call_node_types(self) -> tuple[str, ...]:
        """Python function call node types."""
        return ("call",)

    @property
    def import_node_types(self) -> tuple[str, ...]:
        """Python import statement node types."""
        return ("import_statement", "import_from_statement")

    @property
    def body_node_type(self) -> str:
        """Python uses 'block' for function/class bodies."""
        return "block"

    # -------------------------------------------------------------------------
    # Python-specific helpers
    # -------------------------------------------------------------------------

    @property
    def decorator_node_types(self) -> tuple[str, ...]:
        """Python decorator node types."""
        return ("decorator",)

    @property
    def async_function_node_types(self) -> tuple[str, ...]:
        """Python async function definition node types."""
        # In tree-sitter-python, async functions are still function_definition
        # The async keyword is captured as a child node
        return ("function_definition",)

    def is_method(self, node_type: str, parent_type: str | None) -> bool:
        """
        Check if a function is actually a method (inside a class).

        Args:
            node_type: The node type string.
            parent_type: The parent node type string.

        Returns:
            True if the function is a method.
        """
        return node_type == "function_definition" and parent_type in (
            "class_definition",
            "block",
        )
