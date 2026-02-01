"""
TreeSitterParser: Tree-sitter wrapper for parsing source files.

This module provides a unified interface for parsing source files
using tree-sitter and executing .scm queries to extract:
- Function definitions
- Class definitions
- Import statements
- Function calls
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from tree_sitter import Parser

from mcp_context_graph.languages.registry import get_language_for_file, get_registry

if TYPE_CHECKING:
    from tree_sitter import Node, Tree

    from mcp_context_graph.languages.base import LanguageConfig

logger = logging.getLogger(__name__)


@dataclass
class ParsedCapture:
    """
    A single capture from a tree-sitter query.

    Attributes:
        node: The tree-sitter node that was captured.
        capture_name: The capture name from the query (e.g., "name", "definition").
        pattern_index: The pattern index in the query.
    """

    node: Node
    capture_name: str
    pattern_index: int


@dataclass
class ParseResult:
    """
    Result of parsing a source file.

    Attributes:
        tree: The parsed syntax tree.
        source_bytes: The original source as bytes.
        language_config: The language configuration used.
        file_path: Path to the source file.
    """

    tree: Tree
    source_bytes: bytes
    language_config: LanguageConfig
    file_path: Path

    @property
    def root_node(self) -> Node:
        """Return the root node of the syntax tree."""
        return self.tree.root_node

    @property
    def source_text(self) -> str:
        """Return source as string."""
        return self.source_bytes.decode("utf-8", errors="replace")


class TreeSitterParser:
    """
    Unified parser wrapper for tree-sitter.

    Provides methods to parse source files and execute queries
    for extracting definitions, calls, and imports.

    Example:
        parser = TreeSitterParser()
        result = parser.parse_file(Path("example.py"))

        for defn in parser.query_definitions(result):
            print(f"Found definition: {defn.node.type}")
    """

    __slots__ = ("_parsers",)

    def __init__(self) -> None:
        """Initialize the parser with empty parser cache."""
        # Cache of parsers by language name
        self._parsers: dict[str, Parser] = {}

    def _get_parser(self, language_config: LanguageConfig) -> Parser:
        """
        Get or create a parser for the given language.

        Args:
            language_config: The language configuration.

        Returns:
            A Parser configured for the language.
        """
        name = language_config.name
        if name not in self._parsers:
            parser = Parser(language_config.language)
            self._parsers[name] = parser
            logger.debug("Created parser for language: %s", name)
        return self._parsers[name]

    def parse_file(self, file_path: Path) -> ParseResult | None:
        """
        Parse a source file using the appropriate tree-sitter grammar.

        Args:
            file_path: Path to the source file.

        Returns:
            ParseResult if successful, None if language not supported
            or parsing fails.
        """
        # Get language config based on file extension
        language_config = get_language_for_file(file_path)
        if language_config is None:
            logger.debug(
                "No language config for extension: %s",
                file_path.suffix,
            )
            return None

        try:
            source_bytes = file_path.read_bytes()
            return self.parse_bytes(source_bytes, language_config, file_path)
        except OSError as e:
            logger.warning("Failed to read file %s: %s", file_path, e)
            return None

    def parse_bytes(
        self,
        source_bytes: bytes,
        language_config: LanguageConfig,
        file_path: Path | None = None,
    ) -> ParseResult:
        """
        Parse source bytes using a specific language grammar.

        Args:
            source_bytes: The source code as bytes.
            language_config: The language configuration to use.
            file_path: Optional path for context.

        Returns:
            ParseResult with the parsed tree.
        """
        parser = self._get_parser(language_config)
        tree = parser.parse(source_bytes)

        logger.debug(
            "Parsed %d bytes as %s",
            len(source_bytes),
            language_config.name,
        )

        return ParseResult(
            tree=tree,
            source_bytes=source_bytes,
            language_config=language_config,
            file_path=file_path or Path("<memory>"),
        )

    def parse_string(
        self,
        source_text: str,
        language: str,
        file_path: Path | None = None,
    ) -> ParseResult | None:
        """
        Parse source string for a specific language.

        Args:
            source_text: The source code as a string.
            language: The language name (e.g., "python").
            file_path: Optional path for context.

        Returns:
            ParseResult if successful, None if language not supported.
        """
        registry = get_registry()
        language_config = registry.get(language)
        if language_config is None:
            logger.warning("Unknown language: %s", language)
            return None

        source_bytes = source_text.encode("utf-8")
        return self.parse_bytes(source_bytes, language_config, file_path)

    # -------------------------------------------------------------------------
    # Query Methods
    # -------------------------------------------------------------------------

    def query_definitions(self, result: ParseResult) -> list[ParsedCapture]:
        """
        Query for function and class definitions.

        Args:
            result: The ParseResult from parsing.

        Returns:
            List of ParsedCapture for each definition found.
        """
        return self._execute_query(result, "definitions")

    def query_calls(self, result: ParseResult) -> list[ParsedCapture]:
        """
        Query for function calls.

        Args:
            result: The ParseResult from parsing.

        Returns:
            List of ParsedCapture for each call found.
        """
        return self._execute_query(result, "calls")

    def query_imports(self, result: ParseResult) -> list[ParsedCapture]:
        """
        Query for import statements.

        Args:
            result: The ParseResult from parsing.

        Returns:
            List of ParsedCapture for each import found.
        """
        return self._execute_query(result, "imports")

    def _execute_query(
        self,
        result: ParseResult,
        query_name: str,
    ) -> list[ParsedCapture]:
        """
        Execute a named query on a parse result.

        Args:
            result: The ParseResult to query.
            query_name: Name of the query (e.g., "definitions").

        Returns:
            List of ParsedCapture objects.
        """
        try:
            query = result.language_config.load_query(query_name)
        except FileNotFoundError:
            logger.debug(
                "Query %r not found for %s",
                query_name,
                result.language_config.name,
            )
            return []

        captures = query.captures(result.root_node)  # type: ignore[attr-defined]

        results: list[ParsedCapture] = []
        for node, capture_name in captures:
            results.append(
                ParsedCapture(
                    node=node,
                    capture_name=capture_name,
                    pattern_index=0,  # tree-sitter captures don't expose pattern index directly
                )
            )

        logger.debug(
            "Query %r on %s: %d captures",
            query_name,
            result.file_path.name,
            len(results),
        )

        return results

    # -------------------------------------------------------------------------
    # Node Extraction Helpers
    # -------------------------------------------------------------------------

    def find_functions(self, result: ParseResult) -> list[Node]:
        """
        Find all function definition nodes in the parse result.

        Args:
            result: The ParseResult to search.

        Returns:
            List of tree-sitter nodes for function definitions.
        """
        config = result.language_config
        function_types = config.function_node_types

        functions: list[Node] = []
        self._collect_by_type(result.root_node, function_types, functions)

        logger.debug(
            "Found %d functions in %s",
            len(functions),
            result.file_path.name,
        )

        return functions

    def find_classes(self, result: ParseResult) -> list[Node]:
        """
        Find all class definition nodes in the parse result.

        Args:
            result: The ParseResult to search.

        Returns:
            List of tree-sitter nodes for class definitions.
        """
        config = result.language_config
        class_types = config.class_node_types

        classes: list[Node] = []
        self._collect_by_type(result.root_node, class_types, classes)

        logger.debug(
            "Found %d classes in %s",
            len(classes),
            result.file_path.name,
        )

        return classes

    def _collect_by_type(
        self,
        node: Node,
        types: tuple[str, ...],
        results: list[Node],
    ) -> None:
        """
        Recursively collect nodes matching given types.

        Args:
            node: The starting node.
            types: Tuple of type names to match.
            results: List to append matching nodes to.
        """
        if node.type in types:
            results.append(node)

        for child in node.children:
            self._collect_by_type(child, types, results)

    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------

    def get_node_text(self, node: Node, source_bytes: bytes) -> str:
        """
        Extract the text for a specific node.

        Args:
            node: The tree-sitter node.
            source_bytes: The full source bytes.

        Returns:
            The text content of the node.
        """
        return source_bytes[node.start_byte : node.end_byte].decode(
            "utf-8", errors="replace"
        )

    def find_child_by_type(self, node: Node, type_name: str) -> Node | None:
        """
        Find the first child of a node with a specific type.

        Args:
            node: The parent node.
            type_name: The type to search for.

        Returns:
            The first matching child, or None.
        """
        for child in node.children:
            if child.type == type_name:
                return child
        return None

    def find_child_by_field(self, node: Node, field_name: str) -> Node | None:
        """
        Find a child node by its field name.

        Args:
            node: The parent node.
            field_name: The field name to search for.

        Returns:
            The child node if found, or None.
        """
        return node.child_by_field_name(field_name)

    def __repr__(self) -> str:
        """Return string representation."""
        languages = list(self._parsers.keys())
        return f"TreeSitterParser(cached_languages={languages})"
