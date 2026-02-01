"""
Normalizer: Captures → GenericNodes conversion.

This module converts tree-sitter captures to generic AST nodes:
- FunctionDeclaration → NodeType.FUNCTION
- ClassDef → NodeType.CLASS
- Preserves source locations (byte offsets)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from mcp_context_graph.core.node import NodeType, SourceLocation

if TYPE_CHECKING:
    from tree_sitter import Node

    from mcp_context_graph.ingest.tree_sitter_parser import ParseResult
    from mcp_context_graph.languages.base import LanguageConfig

logger = logging.getLogger(__name__)


@dataclass
class GenericNode:
    """
    Language-agnostic representation of an AST node.

    This is an intermediate representation that abstracts over
    language-specific tree-sitter node types.

    Attributes:
        type: The generic node type (FUNCTION, CLASS, etc.)
        name: The symbol name (e.g., function or class name)
        qualified_name: Fully qualified name including parent scope
        language: The source language
        location: Source location with byte offsets
        ts_node: The original tree-sitter node
        signature_end: Byte offset where signature ends (for minification)
        body_start: Byte offset where body starts
        body_end: Byte offset where body ends
        parent_name: Name of the parent scope (if any)
        parameters: Function parameters as string
        return_type: Return type annotation (if available)
        docstring: Docstring content (if available)
    """

    type: NodeType
    name: str
    qualified_name: str
    language: str
    location: SourceLocation
    ts_node: Node
    signature_end: int
    body_start: int
    body_end: int
    parent_name: str | None = None
    parameters: str | None = None
    return_type: str | None = None
    docstring: str | None = None


@dataclass
class NormalizationResult:
    """
    Result of normalizing a parse result.

    Attributes:
        functions: List of function definitions
        classes: List of class definitions
        methods: List of method definitions (functions inside classes)
        imports: List of import statements
        calls: List of function calls
    """

    functions: list[GenericNode] = field(default_factory=list)
    classes: list[GenericNode] = field(default_factory=list)
    methods: list[GenericNode] = field(default_factory=list)
    imports: list[GenericNode] = field(default_factory=list)
    calls: list[GenericNode] = field(default_factory=list)

    @property
    def all_definitions(self) -> list[GenericNode]:
        """Return all definition nodes (functions, classes, methods)."""
        return self.functions + self.classes + self.methods


class Normalizer:
    """
    Converts tree-sitter parse results to generic AST nodes.

    The normalizer provides a language-agnostic interface for
    extracting code structure information from tree-sitter parses.

    Example:
        parser = TreeSitterParser()
        result = parser.parse_file(Path("example.py"))

        normalizer = Normalizer()
        normalized = normalizer.normalize(result)

        for func in normalized.functions:
            print(f"Function: {func.name}")
    """

    def __init__(self) -> None:
        """Initialize the normalizer."""
        pass

    def normalize(self, parse_result: ParseResult) -> NormalizationResult:
        """
        Normalize a parse result to generic nodes.

        Args:
            parse_result: The ParseResult from TreeSitterParser.

        Returns:
            NormalizationResult with extracted definitions.
        """
        result = NormalizationResult()
        config = parse_result.language_config
        source_bytes = parse_result.source_bytes
        language = config.name

        # Find class definitions first to track parent scope
        class_map: dict[int, str] = {}  # start_byte -> class_name
        self._process_classes(
            parse_result.root_node,
            config,
            source_bytes,
            language,
            result,
            class_map,
        )

        # Find function definitions
        self._process_functions(
            parse_result.root_node,
            config,
            source_bytes,
            language,
            result,
            class_map,
        )

        # Process imports
        self._process_imports(
            parse_result.root_node,
            config,
            source_bytes,
            language,
            result,
        )

        logger.debug(
            "Normalized %s: %d functions, %d classes, %d methods, %d imports",
            parse_result.file_path.name,
            len(result.functions),
            len(result.classes),
            len(result.methods),
            len(result.imports),
        )

        return result

    def _process_classes(
        self,
        root_node: Node,
        config: LanguageConfig,
        source_bytes: bytes,
        language: str,
        result: NormalizationResult,
        class_map: dict[int, str],
    ) -> None:
        """Process class definitions in the AST."""
        class_types = config.class_node_types

        for node in self._walk_tree(root_node, class_types):
            generic = self._node_to_generic_class(node, config, source_bytes, language)
            if generic:
                result.classes.append(generic)
                # Track class scope by its body range
                body_node = self._find_body_node(node, config)
                if body_node:
                    class_map[body_node.start_byte] = generic.name

    def _process_functions(
        self,
        root_node: Node,
        config: LanguageConfig,
        source_bytes: bytes,
        language: str,
        result: NormalizationResult,
        class_map: dict[int, str],
    ) -> None:
        """Process function definitions in the AST."""
        function_types = config.function_node_types

        for node in self._walk_tree(root_node, function_types):
            # Check if this function is inside a class
            parent_class = self._find_parent_class(node, class_map, config)

            generic = self._node_to_generic_function(
                node, config, source_bytes, language, parent_class
            )
            if generic:
                if parent_class:
                    result.methods.append(generic)
                else:
                    result.functions.append(generic)

    def _process_imports(
        self,
        root_node: Node,
        config: LanguageConfig,
        source_bytes: bytes,
        language: str,
        result: NormalizationResult,
    ) -> None:
        """Process import statements in the AST."""
        import_types = config.import_node_types

        for node in self._walk_tree(root_node, import_types):
            generic = self._node_to_generic_import(node, config, source_bytes, language)
            if generic:
                result.imports.append(generic)

    def _walk_tree(self, node: Node, types: tuple[str, ...]) -> list[Node]:
        """Recursively collect nodes of given types."""
        matches: list[Node] = []

        if node.type in types:
            matches.append(node)

        for child in node.children:
            matches.extend(self._walk_tree(child, types))

        return matches

    def _node_to_generic_function(
        self,
        node: Node,
        config: LanguageConfig,
        source_bytes: bytes,
        language: str,
        parent_class: str | None = None,
    ) -> GenericNode | None:
        """Convert a function node to GenericNode."""
        # Extract function name
        name = self._extract_function_name(node, source_bytes, language)
        if not name:
            logger.debug("Could not extract name from function node")
            return None

        # Determine qualified name
        if parent_class:
            qualified_name = f"{parent_class}.{name}"
            node_type = NodeType.METHOD
        else:
            qualified_name = name
            node_type = NodeType.FUNCTION

        # Find body and signature boundaries
        body_node = self._find_body_node(node, config)
        signature_end, body_start, body_end = self._compute_boundaries(
            node, body_node, source_bytes, language
        )

        # Extract additional info
        parameters = self._extract_parameters(node, source_bytes, language)
        return_type = self._extract_return_type(node, source_bytes, language)

        location = SourceLocation(
            file_path="",  # Will be filled in by caller
            start_byte=node.start_byte,
            end_byte=node.end_byte,
            start_line=node.start_point[0] + 1,
            start_column=node.start_point[1],
            end_line=node.end_point[0] + 1,
            end_column=node.end_point[1],
        )

        return GenericNode(
            type=node_type,
            name=name,
            qualified_name=qualified_name,
            language=language,
            location=location,
            ts_node=node,
            signature_end=signature_end,
            body_start=body_start,
            body_end=body_end,
            parent_name=parent_class,
            parameters=parameters,
            return_type=return_type,
        )

    def _node_to_generic_class(
        self,
        node: Node,
        config: LanguageConfig,
        source_bytes: bytes,
        language: str,
    ) -> GenericNode | None:
        """Convert a class node to GenericNode."""
        name = self._extract_class_name(node, source_bytes, language)
        if not name:
            logger.debug("Could not extract name from class node")
            return None

        # Find body boundaries
        body_node = self._find_body_node(node, config)
        signature_end, body_start, body_end = self._compute_boundaries(
            node, body_node, source_bytes, language
        )

        location = SourceLocation(
            file_path="",
            start_byte=node.start_byte,
            end_byte=node.end_byte,
            start_line=node.start_point[0] + 1,
            start_column=node.start_point[1],
            end_line=node.end_point[0] + 1,
            end_column=node.end_point[1],
        )

        return GenericNode(
            type=NodeType.CLASS,
            name=name,
            qualified_name=name,
            language=language,
            location=location,
            ts_node=node,
            signature_end=signature_end,
            body_start=body_start,
            body_end=body_end,
        )

    def _node_to_generic_import(
        self,
        node: Node,
        config: LanguageConfig,  # noqa: ARG002 - reserved for future use
        source_bytes: bytes,
        language: str,
    ) -> GenericNode | None:
        """Convert an import node to GenericNode."""
        name = self._extract_import_name(node, source_bytes, language)
        if not name:
            return None

        location = SourceLocation(
            file_path="",
            start_byte=node.start_byte,
            end_byte=node.end_byte,
            start_line=node.start_point[0] + 1,
            start_column=node.start_point[1],
            end_line=node.end_point[0] + 1,
            end_column=node.end_point[1],
        )

        return GenericNode(
            type=NodeType.IMPORT,
            name=name,
            qualified_name=name,
            language=language,
            location=location,
            ts_node=node,
            signature_end=node.end_byte,
            body_start=node.end_byte,
            body_end=node.end_byte,
        )

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def _find_body_node(self, node: Node, config: LanguageConfig) -> Node | None:
        """Find the body node within a function or class."""
        body_type = config.body_node_type

        for child in node.children:
            if child.type == body_type:
                return child

        # Try common alternatives
        alternatives = ("block", "statement_block", "class_body", "body")
        for alt in alternatives:
            for child in node.children:
                if child.type == alt:
                    return child

        return None

    def _find_parent_class(
        self,
        node: Node,
        class_map: dict[int, str],
        config: LanguageConfig,  # noqa: ARG002 - reserved for future use
    ) -> str | None:
        """Determine if a node is inside a class body."""
        parent = node.parent
        while parent:
            if parent.start_byte in class_map:
                return class_map[parent.start_byte]
            parent = parent.parent
        return None

    def _compute_boundaries(
        self,
        node: Node,
        body_node: Node | None,
        source_bytes: bytes,
        language: str,
    ) -> tuple[int, int, int]:
        """
        Compute signature end, body start, and body end boundaries.

        Returns:
            Tuple of (signature_end, body_start, body_end)
        """
        if body_node is None:
            # No body found, use full node
            return node.end_byte, node.end_byte, node.end_byte

        body_start = body_node.start_byte
        body_end = body_node.end_byte

        # For Python, signature_end is right before the body (at the colon)
        # For JS/TS, it's right before the opening brace
        if language == "python":
            # Find the colon before the body
            pre_body = source_bytes[node.start_byte : body_start].decode(
                "utf-8", errors="replace"
            )
            colon_pos = pre_body.rfind(":")
            signature_end = (
                node.start_byte + colon_pos + 1 if colon_pos >= 0 else body_start
            )
        else:
            # JS/TS: signature ends before opening brace
            signature_end = body_start

        return signature_end, body_start, body_end

    def _extract_function_name(
        self,
        node: Node,
        source_bytes: bytes,
        language: str,
    ) -> str | None:
        """Extract function name from node."""
        # Try field name first
        name_node = node.child_by_field_name("name")
        if name_node:
            return source_bytes[name_node.start_byte : name_node.end_byte].decode(
                "utf-8", errors="replace"
            )

        # Python and similar: look for identifier after 'def'
        if language == "python":
            for child in node.children:
                if child.type == "identifier":
                    return source_bytes[child.start_byte : child.end_byte].decode(
                        "utf-8", errors="replace"
                    )

        # JS/TS: function name
        for child in node.children:
            if child.type in ("identifier", "property_identifier"):
                return source_bytes[child.start_byte : child.end_byte].decode(
                    "utf-8", errors="replace"
                )

        # Arrow functions might not have names
        return None

    def _extract_class_name(
        self,
        node: Node,
        source_bytes: bytes,
        language: str,  # noqa: ARG002 - reserved for future use
    ) -> str | None:
        """Extract class name from node."""
        name_node = node.child_by_field_name("name")
        if name_node:
            return source_bytes[name_node.start_byte : name_node.end_byte].decode(
                "utf-8", errors="replace"
            )

        for child in node.children:
            if child.type in ("identifier", "type_identifier"):
                return source_bytes[child.start_byte : child.end_byte].decode(
                    "utf-8", errors="replace"
                )

        return None

    def _extract_import_name(
        self,
        node: Node,
        source_bytes: bytes,
        language: str,
    ) -> str | None:
        """Extract imported module/symbol name from import node."""
        # Get the full import text as a fallback
        full_text = source_bytes[node.start_byte : node.end_byte].decode(
            "utf-8", errors="replace"
        )

        if language == "python":
            # For "import X" or "from X import Y"
            for child in node.children:
                if child.type == "dotted_name":
                    return source_bytes[child.start_byte : child.end_byte].decode(
                        "utf-8", errors="replace"
                    )
                if child.type == "aliased_import":
                    # Extract original name
                    for subchild in child.children:
                        if subchild.type == "dotted_name":
                            return source_bytes[
                                subchild.start_byte : subchild.end_byte
                            ].decode("utf-8", errors="replace")

        # Return full text as fallback
        return full_text.split("\n")[0].strip()[:50]

    def _extract_parameters(
        self,
        node: Node,
        source_bytes: bytes,
        language: str,  # noqa: ARG002 - reserved for future use
    ) -> str | None:
        """Extract function parameters as string."""
        # Look for parameters node
        params_node = node.child_by_field_name("parameters")
        if params_node:
            return source_bytes[params_node.start_byte : params_node.end_byte].decode(
                "utf-8", errors="replace"
            )

        for child in node.children:
            if child.type in ("parameters", "formal_parameters"):
                return source_bytes[child.start_byte : child.end_byte].decode(
                    "utf-8", errors="replace"
                )

        return None

    def _extract_return_type(
        self,
        node: Node,
        source_bytes: bytes,
        language: str,  # noqa: ARG002 - reserved for future use
    ) -> str | None:
        """Extract return type annotation if present."""
        return_type = node.child_by_field_name("return_type")
        if return_type:
            return source_bytes[return_type.start_byte : return_type.end_byte].decode(
                "utf-8", errors="replace"
            )

        # Try type annotation
        for child in node.children:
            if child.type in ("type", "type_annotation"):
                return source_bytes[child.start_byte : child.end_byte].decode(
                    "utf-8", errors="replace"
                )

        return None

    def __repr__(self) -> str:
        """Return string representation."""
        return "Normalizer()"
