"""
LanguageConfig base class for language configurations.

Defines the interface for language-specific configurations including:
- Tree-sitter grammar loading
- Query file paths for definitions, calls, imports
- Language-specific node type mappings
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tree_sitter import Language, Query

logger = logging.getLogger(__name__)


class LanguageConfig(ABC):
    """
    Abstract base class for language-specific configurations.

    Each supported language must implement this class to provide:
    - Tree-sitter Language object
    - Paths to .scm query files
    - Node type mappings for normalization

    Subclasses are expected to be singletons (one per language).
    """

    __slots__ = ("_language", "_queries_dir", "_cached_queries")

    def __init__(self, queries_dir: Path | None = None) -> None:
        """
        Initialize the language configuration.

        Args:
            queries_dir: Path to directory containing .scm query files.
                        If None, uses the default location next to config.py.
        """
        self._language: Language | None = None
        self._queries_dir = queries_dir or self._default_queries_dir()
        self._cached_queries: dict[str, Query] = {}

        logger.debug(
            "Initialized %s with queries_dir=%s",
            self.__class__.__name__,
            self._queries_dir,
        )

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Return the canonical language name.

        Returns:
            Language name string (e.g., "python", "typescript", "javascript").
        """
        ...

    @property
    @abstractmethod
    def file_extensions(self) -> tuple[str, ...]:
        """
        Return the file extensions this language handles.

        Returns:
            Tuple of extensions with leading dots (e.g., (".py", ".pyw")).
        """
        ...

    @abstractmethod
    def _default_queries_dir(self) -> Path:
        """
        Return the default path to the queries directory.

        Returns:
            Path to the queries/ directory for this language.
        """
        ...

    @abstractmethod
    def _load_language(self) -> Language:
        """
        Load and return the tree-sitter Language object.

        Returns:
            The Language object for this language.
        """
        ...

    @property
    def language(self) -> Language:
        """
        Get the tree-sitter Language object (lazy loading).

        Returns:
            The Language object for parsing.
        """
        if self._language is None:
            self._language = self._load_language()
            logger.debug("Loaded tree-sitter language: %s", self.name)
        return self._language

    def get_query_path(self, query_name: str) -> Path:
        """
        Get the path to a specific .scm query file.

        Args:
            query_name: Name of the query without extension
                       (e.g., "definitions", "calls", "imports").

        Returns:
            Path to the .scm file.

        Raises:
            FileNotFoundError: If the query file doesn't exist.
        """
        query_path = self._queries_dir / f"{query_name}.scm"
        if not query_path.exists():
            msg = f"Query file not found: {query_path}"
            raise FileNotFoundError(msg)
        return query_path

    def load_query(self, query_name: str) -> Query:
        """
        Load and compile a tree-sitter query from .scm file.

        Uses caching to avoid re-compiling the same query.

        Args:
            query_name: Name of the query (e.g., "definitions").

        Returns:
            Compiled Query object.

        Raises:
            FileNotFoundError: If query file doesn't exist.
            tree_sitter.QueryError: If query syntax is invalid.
        """
        if query_name in self._cached_queries:
            return self._cached_queries[query_name]

        query_path = self.get_query_path(query_name)
        query_text = query_path.read_text(encoding="utf-8")

        # Import here to avoid circular imports
        from tree_sitter import Language as TSLanguage

        query = TSLanguage(self.language).query(query_text)
        self._cached_queries[query_name] = query

        logger.debug(
            "Loaded query '%s' for %s (%d patterns)",
            query_name,
            self.name,
            len(query.patterns),  # type: ignore[attr-defined]
        )
        return query

    def get_definitions_query(self) -> Query:
        """Load the definitions query."""
        return self.load_query("definitions")

    def get_calls_query(self) -> Query:
        """Load the calls query."""
        return self.load_query("calls")

    def get_imports_query(self) -> Query:
        """Load the imports query."""
        return self.load_query("imports")

    # -------------------------------------------------------------------------
    # Node Type Mappings (can be overridden by subclasses)
    # -------------------------------------------------------------------------

    @property
    def function_node_types(self) -> tuple[str, ...]:
        """
        Return tree-sitter node types that represent function definitions.

        Returns:
            Tuple of node type strings.
        """
        # Default for Python-style languages
        return ("function_definition",)

    @property
    def class_node_types(self) -> tuple[str, ...]:
        """
        Return tree-sitter node types that represent class definitions.

        Returns:
            Tuple of node type strings.
        """
        return ("class_definition",)

    @property
    def call_node_types(self) -> tuple[str, ...]:
        """
        Return tree-sitter node types that represent function calls.

        Returns:
            Tuple of node type strings.
        """
        return ("call",)

    @property
    def import_node_types(self) -> tuple[str, ...]:
        """
        Return tree-sitter node types that represent imports.

        Returns:
            Tuple of node type strings.
        """
        return ("import_statement", "import_from_statement")

    @property
    def body_node_type(self) -> str:
        """
        Return the node type for function/class bodies.

        This is used by the minifier to identify what to replace.

        Returns:
            Node type string for body blocks.
        """
        return "block"

    def __repr__(self) -> str:
        """Return string representation."""
        return f"{self.__class__.__name__}(name={self.name!r})"
