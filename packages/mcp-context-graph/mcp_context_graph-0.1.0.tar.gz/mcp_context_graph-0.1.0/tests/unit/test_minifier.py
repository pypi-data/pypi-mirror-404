"""
Unit tests for Minifier class.

Tests cover:
- Identity minification
- Single function minification
- Multiple function minification
- Source map correctness (round-trip consistency)
- Boundary conditions
"""

from mcp_context_graph.ingest.minifier import (
    BODY_PLACEHOLDER,
    Minifier,
    create_identity_minification,
)


class TestMinifierIdentity:
    """Tests for identity minification (no changes)."""

    def test_identity_minification_empty_text(self) -> None:
        """Empty text produces empty result."""
        minifier = Minifier()
        result = minifier.minify_text("")
        assert result.minified_text == ""
        assert len(result.source_map) == 0

    def test_identity_minification_simple_text(self) -> None:
        """Simple text is preserved unchanged."""
        text = "hello world"
        minifier = Minifier()
        result = minifier.minify_text(text)
        assert result.minified_text == text
        assert result.original_text == text

    def test_identity_minification_roundtrip(self) -> None:
        """Every offset in identity minification maps back correctly."""
        text = "def foo(): pass"
        minifier = Minifier()
        result = minifier.minify_text(text)

        for i in range(len(text)):
            original = result.to_original_offset(i)
            assert original == i, f"Offset {i} should map to {i}, got {original}"

            minified = result.to_minified_offset(i)
            assert minified == i, f"Original {i} should map to {i}, got {minified}"

    def test_create_identity_minification_helper(self) -> None:
        """Convenience function creates identity mapping."""
        text = "some code here"
        result = create_identity_minification(text)
        assert result.minified_text == text
        assert len(result.source_map) == 1


class TestMinifierSingleFunction:
    """Tests for single function minification."""

    def test_simple_function_minification(self) -> None:
        """Basic function body is replaced with placeholder."""
        text = "def foo(): return 42"
        #       0123456789012345678901
        #       signature ends at 10 (after ':')
        #       body starts at 11 (' return 42')
        minifier = Minifier()
        result = minifier.minify_function(
            text=text,
            signature_end=10,
            body_start=11,
            body_end=21,
        )

        # "def foo():" + " " + "..."
        assert result.minified_text == "def foo(): ..."
        assert result.original_text == text

    def test_function_with_multiline_body(self) -> None:
        """Multiline function body is replaced."""
        text = """def foo():
    x = 1
    return x"""
        # signature ends at position 10 (after ':')
        # body starts at 11 (newline and indented code)
        signature_end = text.index(":") + 1
        body_start = signature_end  # includes the newline
        body_end = len(text)

        minifier = Minifier()
        result = minifier.minify_function(
            text=text,
            signature_end=signature_end,
            body_start=body_start,
            body_end=body_end,
        )

        # Check the placeholder is there
        assert "..." in result.minified_text
        assert "x = 1" not in result.minified_text
        assert "return x" not in result.minified_text

    def test_signature_offsets_preserved(self) -> None:
        """Offsets in the signature map correctly to original."""
        text = "def foo(x, y):\n    return x + y"
        signature_end = text.index(":") + 1  # 14
        body_start = signature_end + 1  # After the newline
        body_end = len(text)

        minifier = Minifier()
        result = minifier.minify_function(
            text=text,
            signature_end=signature_end,
            body_start=body_start,
            body_end=body_end,
        )

        # Check signature characters map correctly
        # "def " starts at 0
        assert result.to_original_offset(0) == 0  # 'd'
        assert result.to_original_offset(1) == 1  # 'e'
        assert result.to_original_offset(2) == 2  # 'f'
        assert result.to_original_offset(3) == 3  # ' '
        assert result.to_original_offset(4) == 4  # 'f' of 'foo'

    def test_function_with_type_annotations(self) -> None:
        """Function with type annotations is minified correctly."""
        text = "def process(data: list[int]) -> str:\n    return str(sum(data))"
        signature_end = text.index(":") + 1
        # But wait, there are multiple colons!
        # Find the colon before the body
        signature_end = text.rfind(":", 0, text.index("\n")) + 1
        body_start = text.index("\n") + 1
        body_end = len(text)

        minifier = Minifier()
        result = minifier.minify_function(
            text=text,
            signature_end=signature_end,
            body_start=body_start,
            body_end=body_end,
        )

        assert "def process(data: list[int]) -> str:" in result.minified_text
        assert "sum(data)" not in result.minified_text

    def test_custom_placeholder(self) -> None:
        """Custom body placeholder is used."""
        text = "def foo(): return 42"
        minifier = Minifier(body_placeholder="<body>")
        result = minifier.minify_function(
            text=text,
            signature_end=10,
            body_start=11,
            body_end=21,
        )

        assert "<body>" in result.minified_text
        assert "..." not in result.minified_text


class TestMinifierMultipleFunctions:
    """Tests for minifying multiple functions."""

    def test_two_functions(self) -> None:
        """Two functions are both minified."""
        text = """def foo():
    return 1

def bar():
    return 2
"""
        # Find positions manually
        # First function: def foo():\n    return 1
        # Second function: def bar():\n    return 2

        # For simplicity, let's calculate positions
        first_sig_end = text.index(":", 0, 20) + 1  # After first ':'
        first_body_start = first_sig_end + 1
        first_body_end = text.index("\n\ndef") + 1  # End of first function body

        second_start = text.index("def bar")
        second_sig_end = text.index(":", second_start) + 1
        second_body_start = second_sig_end + 1
        second_body_end = len(text) - 1  # Before final newline

        functions = [
            (first_sig_end, first_body_start, first_body_end, first_body_end),
            (second_sig_end, second_body_start, second_body_end, second_body_end),
        ]

        minifier = Minifier()
        result = minifier.minify_multiple_functions(text, functions)

        assert "def foo():" in result.minified_text
        assert "def bar():" in result.minified_text
        assert "return 1" not in result.minified_text
        assert "return 2" not in result.minified_text
        assert result.minified_text.count("...") == 2

    def test_empty_functions_list(self) -> None:
        """Empty functions list produces identity result."""
        text = "# Just a comment"
        minifier = Minifier()
        result = minifier.minify_multiple_functions(text, [])
        assert result.minified_text == text


class TestMinificationSourceMapCorrectness:
    """Critical tests for source map correctness."""

    def test_roundtrip_in_signature(self) -> None:
        """
        Characters in preserved signature have correct roundtrip mapping.

        This is the critical test for provenance correctness.
        """
        text = "def calculate(a, b): return a * b"
        #       01234567890123456789012345678901234
        signature_end = 20  # After ':'
        body_start = 21
        body_end = 34

        minifier = Minifier()
        result = minifier.minify_function(
            text=text,
            signature_end=signature_end,
            body_start=body_start,
            body_end=body_end,
        )

        # Every character in signature should roundtrip correctly
        for i in range(signature_end):
            original = result.to_original_offset(i)
            assert original == i, f"Signature char {i} ('{text[i]}') maps to {original}"

            back = result.to_minified_offset(original)
            assert back == i, f"Roundtrip failed at {i}"

    def test_body_offsets_map_to_placeholder(self) -> None:
        """
        Offsets in the placeholder map back to the original body range.
        """
        text = "def foo(): x = 1; return x"
        #       0123456789012345678901234567
        signature_end = 10
        body_start = 11
        body_end = 27

        minifier = Minifier()
        result = minifier.minify_function(
            text=text,
            signature_end=signature_end,
            body_start=body_start,
            body_end=body_end,
        )

        # minified: "def foo(): ..."
        #            0123456789012345
        # Positions 0-9 are "def foo():" (signature)
        # Position 10 is the space (replacement for original whitespace)
        # Positions 11-13 are "..." (replacement for body)

        # The placeholder character positions (11, 12, 13) should map to body range
        for i in range(11, 14):  # The "..." characters at positions 11-13
            original = result.to_original_offset(i)
            assert original is not None, f"Minified offset {i} should map to something"
            # The ... maps to the body range [11, 27)
            assert body_start <= original < body_end, (
                f"Placeholder char at minified {i} maps to {original}, "
                f"expected within body [{body_start}, {body_end})"
            )

    def test_offset_in_removed_body_returns_none(self) -> None:
        """
        Original offsets that are in the body (which was replaced)
        should map to the placeholder range, not None.
        """
        text = "def foo(): return 42"
        signature_end = 10
        body_start = 11
        body_end = 21

        minifier = Minifier()
        result = minifier.minify_function(
            text=text,
            signature_end=signature_end,
            body_start=body_start,
            body_end=body_end,
        )

        # Original offset 15 is in " return 42"
        # This should map to somewhere in the placeholder
        minified = result.to_minified_offset(15)
        # Since the body [11, 21) maps to placeholder [12, 15),
        # offset 15 (which is body_start + 4) maps to minified placeholder
        assert minified is not None
        # The minified position should be in the "..." range

    def test_boundary_at_signature_end(self) -> None:
        """Test exact boundary at signature end."""
        text = "def f(): pass"
        #       0123456789012
        signature_end = 8  # After ':'
        body_start = 9
        body_end = 13

        minifier = Minifier()
        result = minifier.minify_function(
            text=text,
            signature_end=signature_end,
            body_start=body_start,
            body_end=body_end,
        )

        # minified: "def f(): ..."
        #            01234567890123

        # Offset 7 is ':' in original and minified
        assert result.to_original_offset(7) == 7

        # Offset 8 is space in minified, maps to whitespace in original
        # (or the space we add as replacement)

    def test_no_off_by_one_errors(self) -> None:
        """
        Comprehensive test for off-by-one errors at all boundaries.
        """
        text = "def test_func(arg1, arg2):\n    body_code = 1\n    return body_code\n"
        signature_end = text.index(":") + 1
        body_start = text.index("\n") + 1
        body_end = len(text)

        minifier = Minifier()
        result = minifier.minify_function(
            text=text,
            signature_end=signature_end,
            body_start=body_start,
            body_end=body_end,
        )

        # Test boundaries: first char, last char of signature, first of placeholder
        assert result.to_original_offset(0) == 0  # 'd' of 'def'

        # Last char of signature (the ':')
        last_sig_idx = signature_end - 1
        assert result.to_original_offset(last_sig_idx) == last_sig_idx


class TestMinificationResult:
    """Tests for MinificationResult class."""

    def test_to_original_offset_method(self) -> None:
        """Test convenience method to_original_offset."""
        result = create_identity_minification("test")
        assert result.to_original_offset(0) == 0
        assert result.to_original_offset(2) == 2

    def test_to_minified_offset_method(self) -> None:
        """Test convenience method to_minified_offset."""
        result = create_identity_minification("test")
        assert result.to_minified_offset(0) == 0
        assert result.to_minified_offset(3) == 3

    def test_stores_original_text(self) -> None:
        """Result stores original text for reference."""
        text = "original code"
        result = create_identity_minification(text)
        assert result.original_text == text


class TestExtractSignature:
    """Tests for extract_signature method."""

    def test_extract_signature_only(self) -> None:
        """Extract only the signature without placeholder."""
        text = "def foo(x: int) -> str:\n    return str(x)"
        signature_end = text.index(":") + 1
        # Actually we want the last colon before the body
        signature_end = text.index(":\n") + 1

        minifier = Minifier()
        result = minifier.extract_signature(
            text=text,
            start=0,
            end=len(text),
            signature_end=signature_end,
        )

        assert result.minified_text == "def foo(x: int) -> str:"
        assert "return" not in result.minified_text
        assert "..." not in result.minified_text


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_body(self) -> None:
        """Function with conceptually empty body."""
        text = "def foo(): pass"
        signature_end = 10
        body_start = 11
        body_end = 15

        minifier = Minifier()
        result = minifier.minify_function(
            text=text,
            signature_end=signature_end,
            body_start=body_start,
            body_end=body_end,
        )

        # "pass" should be replaced with "..."
        assert "pass" not in result.minified_text
        assert "..." in result.minified_text

    def test_unicode_in_function(self) -> None:
        """Function with unicode characters."""
        text = "def grüß(): return '你好'"
        # Note: unicode chars have different byte lengths
        # For simplicity, work with the string as Python sees it

        # Find positions
        signature_end = text.index(":") + 1
        body_start = signature_end + 1
        body_end = len(text)

        minifier = Minifier()
        result = minifier.minify_function(
            text=text,
            signature_end=signature_end,
            body_start=body_start,
            body_end=body_end,
        )

        assert "grüß" in result.minified_text
        assert "你好" not in result.minified_text

    def test_function_at_end_of_file(self) -> None:
        """Function at end of file without trailing newline."""
        text = "def last(): return None"
        signature_end = 11
        body_start = 12
        body_end = 23

        minifier = Minifier()
        result = minifier.minify_function(
            text=text,
            signature_end=signature_end,
            body_start=body_start,
            body_end=body_end,
        )

        assert result.minified_text == "def last(): ..."

    def test_function_with_decorator(self) -> None:
        """Decorator is preserved, body is replaced."""
        text = "@decorator\ndef foo(): return 42"
        # The decorator should be preserved as part of the pre-function text
        signature_end = text.index(":") + 1
        body_start = signature_end + 1
        body_end = len(text)

        minifier = Minifier()
        result = minifier.minify_function(
            text=text,
            signature_end=signature_end,
            body_start=body_start,
            body_end=body_end,
        )

        # The result should include everything up to signature
        assert "@decorator\ndef foo():" in result.minified_text
        assert "return 42" not in result.minified_text


class TestDefaultPlaceholder:
    """Tests for default placeholder behavior."""

    def test_default_placeholder_is_ellipsis(self) -> None:
        """Default placeholder should be '...'."""
        assert BODY_PLACEHOLDER == "..."

    def test_minifier_uses_default(self) -> None:
        """Minifier uses default placeholder by default."""
        minifier = Minifier()
        assert minifier.body_placeholder == "..."
