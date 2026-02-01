"""
Minifier: Signature extraction with source map generation.

This module extracts minimal signatures from AST nodes while
generating source maps for character-level provenance tracking:
- Extract function/class signature only
- Build SourceMap: List[Segment]
- Segment = (minified_start, minified_end, original_start, original_end)

The minifier produces a "signature view" of code where function bodies
are replaced with "..." while preserving exact byte offsets for any
preserved text, enabling character-level provenance back to the original.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from mcp_context_graph.provenance.segment import Segment
from mcp_context_graph.provenance.source_map import SourceMap

if TYPE_CHECKING:
    from tree_sitter import Node

logger = logging.getLogger(__name__)


# Body placeholder used when minifying function/method bodies
BODY_PLACEHOLDER = "..."


@dataclass
class MinificationResult:
    """
    Result of minifying source code.

    Attributes:
        minified_text: The minified source code with bodies replaced
        source_map: SourceMap for bidirectional offset mapping
        original_text: The original source code for reference
    """

    minified_text: str
    source_map: SourceMap
    original_text: str

    def to_original_offset(self, minified_offset: int) -> int | None:
        """Map a minified offset back to the original source."""
        return self.source_map.minified_to_original(minified_offset)

    def to_minified_offset(self, original_offset: int) -> int | None:
        """Map an original offset to the minified source."""
        return self.source_map.original_to_minified(original_offset)


@dataclass
class _MinifierState:
    """
    Internal state for minification process.

    Tracks current positions in both original and minified text
    as we build the output incrementally.
    """

    original_text: str
    segments: list[Segment] = field(default_factory=list)
    minified_chunks: list[str] = field(default_factory=list)
    minified_pos: int = 0
    last_original_pos: int = 0

    def add_preserved_range(self, original_start: int, original_end: int) -> None:
        """
        Add a range of text that is preserved verbatim.

        Args:
            original_start: Start offset in original text
            original_end: End offset in original text
        """
        if original_end <= original_start:
            return

        text = self.original_text[original_start:original_end]
        length = len(text)

        segment = Segment(
            minified_start=self.minified_pos,
            minified_end=self.minified_pos + length,
            original_start=original_start,
            original_end=original_end,
        )
        self.segments.append(segment)
        self.minified_chunks.append(text)
        self.minified_pos += length
        self.last_original_pos = original_end

        logger.debug(
            "Preserved range: original[%d:%d] -> minified[%d:%d] = %r",
            original_start,
            original_end,
            segment.minified_start,
            segment.minified_end,
            text[:50] + "..." if len(text) > 50 else text,
        )

    def add_replacement(
        self,
        original_start: int,
        original_end: int,
        replacement: str,
    ) -> None:
        """
        Add a replacement for a range of original text.

        The replacement text is added to the minified output, and a segment
        is created to track that the replacement corresponds to the original range.

        Args:
            original_start: Start offset in original text
            original_end: End offset in original text
            replacement: Replacement text (e.g., "...")
        """
        if not replacement:
            # Skip empty replacements, just update position
            self.last_original_pos = original_end
            return

        # The replacement maps to the original range
        segment = Segment(
            minified_start=self.minified_pos,
            minified_end=self.minified_pos + len(replacement),
            original_start=original_start,
            original_end=original_end,
        )
        self.segments.append(segment)
        self.minified_chunks.append(replacement)
        self.minified_pos += len(replacement)
        self.last_original_pos = original_end

        logger.debug(
            "Replacement: original[%d:%d] -> minified[%d:%d] = %r",
            original_start,
            original_end,
            segment.minified_start,
            segment.minified_end,
            replacement,
        )

    def skip_range(self, original_start: int, original_end: int) -> None:
        """
        Skip a range of original text (remove it completely).

        No segment is created for skipped ranges - they become gaps
        in the source map where lookups return None.

        Args:
            original_start: Start offset in original text
            original_end: End offset in original text
        """
        self.last_original_pos = original_end
        logger.debug(
            "Skipped range: original[%d:%d]",
            original_start,
            original_end,
        )

    def build_result(self) -> MinificationResult:
        """Build the final MinificationResult."""
        minified_text = "".join(self.minified_chunks)
        source_map = SourceMap(self.segments)

        logger.debug(
            "Built minification result: %d chars -> %d chars, %d segments",
            len(self.original_text),
            len(minified_text),
            len(self.segments),
        )

        return MinificationResult(
            minified_text=minified_text,
            source_map=source_map,
            original_text=self.original_text,
        )


class Minifier:
    """
    Extracts signatures from code while building source maps.

    The Minifier processes source code (with optional tree-sitter AST)
    to produce a "signature view" where function bodies are replaced
    with "..." placeholders, while maintaining character-level provenance
    back to the original source.

    Example:
        Original:
            def foo(x: int) -> str:
                result = str(x)
                return result

        Minified:
            def foo(x: int) -> str: ...

        The source map tracks that characters in the minified output
        map back to their exact positions in the original.
    """

    def __init__(self, body_placeholder: str = BODY_PLACEHOLDER) -> None:
        """
        Initialize the Minifier.

        Args:
            body_placeholder: String to replace function bodies with.
                            Defaults to "..."
        """
        self.body_placeholder = body_placeholder

    def minify_text(self, text: str) -> MinificationResult:
        """
        Create an identity minification (no changes).

        This is useful for files that don't need minification or as a
        fallback when parsing fails.

        Args:
            text: Source code text

        Returns:
            MinificationResult with identity mapping
        """
        state = _MinifierState(original_text=text)
        state.add_preserved_range(0, len(text))
        return state.build_result()

    def minify_function(
        self,
        text: str,
        signature_end: int,
        body_start: int,
        body_end: int,
    ) -> MinificationResult:
        """
        Minify a single function by replacing its body with a placeholder.

        Args:
            text: Full source code text
            signature_end: Byte offset where the signature ends (after ':')
            body_start: Byte offset where the function body starts
            body_end: Byte offset where the function body ends

        Returns:
            MinificationResult with the body replaced

        Example:
            For "def foo(x): return x"
            - signature_end = 11 (after ':')
            - body_start = 12 (start of ' return x')
            - body_end = 21 (end of text)

            Result: "def foo(x): ..."
        """
        state = _MinifierState(original_text=text)

        # Preserve everything up to and including the signature
        state.add_preserved_range(0, signature_end)

        # Add space before placeholder if body doesn't start immediately after colon
        # Check if there's whitespace between colon and body
        if body_start > signature_end:
            whitespace = text[signature_end:body_start]
            if whitespace.strip() == "":
                # Pure whitespace, add just a single space
                state.add_replacement(signature_end, body_start, " ")
            else:
                # Some content between, preserve it
                state.add_preserved_range(signature_end, body_start)

        # Replace the body with placeholder
        state.add_replacement(body_start, body_end, self.body_placeholder)

        # If there's text after the function, preserve it
        if body_end < len(text):
            state.add_preserved_range(body_end, len(text))

        return state.build_result()

    def minify_function_node(
        self,
        text: str,
        node: Node,
        body_node_type: str = "block",
    ) -> MinificationResult:
        """
        Minify a function given its tree-sitter AST node.

        Args:
            text: Full source code text
            node: Tree-sitter node for the function definition
            body_node_type: The node type name for the function body.
                           Defaults to "block" (Python).

        Returns:
            MinificationResult with the body replaced
        """
        # Find the body node
        body_node = None
        for child in node.children:
            if child.type == body_node_type:
                body_node = child
                break

        if body_node is None:
            # No body found, return identity mapping
            logger.warning(
                "No body node of type %r found in function node %r",
                body_node_type,
                node.type,
            )
            return self.minify_text(text[node.start_byte : node.end_byte])

        # Find the colon (end of signature) for Python-style functions
        colon_pos = None
        for child in node.children:
            if child.type == ":" or (hasattr(child, "text") and child.text == b":"):
                colon_pos = child.end_byte
                break

        if colon_pos is None:
            # Try to find colon by looking at text before body
            pre_body = text[node.start_byte : body_node.start_byte]
            colon_idx = pre_body.rfind(":")
            colon_pos = (
                node.start_byte + colon_idx + 1
                if colon_idx >= 0
                else body_node.start_byte
            )

        return self.minify_function(
            text=text,
            signature_end=colon_pos,
            body_start=body_node.start_byte,
            body_end=body_node.end_byte,
        )

    def minify_multiple_functions(
        self,
        text: str,
        functions: list[tuple[int, int, int, int]],
    ) -> MinificationResult:
        """
        Minify multiple functions in a source file.

        Args:
            text: Full source code text
            functions: List of (signature_end, body_start, body_end, func_end)
                      tuples, sorted by position in the file

        Returns:
            MinificationResult with all function bodies replaced

        Note:
            Functions should not overlap and should be sorted by position.
        """
        if not functions:
            return self.minify_text(text)

        # Sort by signature_end to ensure proper ordering
        sorted_funcs = sorted(functions, key=lambda x: x[0])

        state = _MinifierState(original_text=text)
        current_pos = 0

        for sig_end, body_start, body_end, _func_end in sorted_funcs:
            # Preserve text from current position to signature end
            if current_pos < sig_end:
                state.add_preserved_range(current_pos, sig_end)

            # Handle whitespace between signature and body
            if body_start > sig_end:
                whitespace = text[sig_end:body_start]
                if whitespace.strip() == "":
                    state.add_replacement(sig_end, body_start, " ")
                else:
                    state.add_preserved_range(sig_end, body_start)

            # Replace body with placeholder
            state.add_replacement(body_start, body_end, self.body_placeholder)
            current_pos = body_end

        # Preserve any remaining text after the last function
        if current_pos < len(text):
            state.add_preserved_range(current_pos, len(text))

        return state.build_result()

    def extract_signature(
        self,
        text: str,
        start: int,
        end: int,  # noqa: ARG002 - Reserved for future use (e.g., partial extraction)
        signature_end: int,
    ) -> MinificationResult:
        """
        Extract just the signature portion of a definition.

        This is useful when you want only the signature, not even a placeholder.

        Args:
            text: Full source code text
            start: Start byte offset of the definition
            end: End byte offset of the definition (reserved for future use)
            signature_end: Byte offset where signature ends

        Returns:
            MinificationResult containing just the signature
        """
        state = _MinifierState(original_text=text)

        # Only preserve the signature portion
        state.add_preserved_range(start, signature_end)

        return state.build_result()


def create_identity_minification(text: str) -> MinificationResult:
    """
    Create an identity minification where output equals input.

    This is a convenience function for creating a MinificationResult
    that represents unchanged text with 1:1 offset mapping.

    Args:
        text: Source code text

    Returns:
        MinificationResult with identity mapping
    """
    return Minifier().minify_text(text)
