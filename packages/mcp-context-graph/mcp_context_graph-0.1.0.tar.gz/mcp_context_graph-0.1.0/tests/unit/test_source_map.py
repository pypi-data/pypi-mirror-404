"""
Unit tests for SourceMap class.

Tests cover:
- Basic functionality
- Boundary conditions (start/end of segments)
- Gap handling (removed code)
- Edge cases (empty maps, single segment, etc.)
- Error conditions (overlapping segments, invalid ranges)
"""

import pytest

from mcp_context_graph.provenance.segment import Segment
from mcp_context_graph.provenance.source_map import SourceMap


class TestSourceMapInitialization:
    """Tests for SourceMap initialization."""

    def test_empty_initialization(self) -> None:
        """Empty source map should be valid."""
        sm = SourceMap()
        assert len(sm) == 0
        assert not sm
        assert sm.segments == ()

    def test_none_segments_initialization(self) -> None:
        """None segments should create empty source map."""
        sm = SourceMap(segments=None)
        assert len(sm) == 0

    def test_single_segment_initialization(self) -> None:
        """Single segment initialization."""
        seg = Segment(
            minified_start=0,
            minified_end=10,
            original_start=0,
            original_end=10,
        )
        sm = SourceMap(segments=[seg])
        assert len(sm) == 1
        assert sm
        assert sm.segments == (seg,)

    def test_multiple_segments_initialization(self) -> None:
        """Multiple non-overlapping segments."""
        segments = [
            Segment(
                minified_start=0, minified_end=10, original_start=0, original_end=10
            ),
            Segment(
                minified_start=10, minified_end=20, original_start=20, original_end=30
            ),
            Segment(
                minified_start=20, minified_end=30, original_start=40, original_end=50
            ),
        ]
        sm = SourceMap(segments=segments)
        assert len(sm) == 3

    def test_unsorted_segments_get_sorted(self) -> None:
        """Segments provided out of order should be sorted."""
        segments = [
            Segment(
                minified_start=20, minified_end=30, original_start=40, original_end=50
            ),
            Segment(
                minified_start=0, minified_end=10, original_start=0, original_end=10
            ),
            Segment(
                minified_start=10, minified_end=20, original_start=20, original_end=30
            ),
        ]
        sm = SourceMap(segments=segments)
        assert sm.segments[0].minified_start == 0
        assert sm.segments[1].minified_start == 10
        assert sm.segments[2].minified_start == 20

    def test_overlapping_segments_raise_error(self) -> None:
        """Overlapping segments should raise ValueError."""
        segments = [
            Segment(
                minified_start=0, minified_end=15, original_start=0, original_end=15
            ),
            Segment(
                minified_start=10, minified_end=20, original_start=20, original_end=30
            ),
        ]
        with pytest.raises(ValueError, match="Overlapping"):
            SourceMap(segments=segments)

    def test_negative_offset_raises_error(self) -> None:
        """Negative offsets should raise ValueError."""
        seg = Segment(
            minified_start=-1,
            minified_end=10,
            original_start=0,
            original_end=10,
        )
        with pytest.raises(ValueError, match="negative"):
            SourceMap(segments=[seg])

    def test_invalid_minified_range_raises_error(self) -> None:
        """Invalid minified range (end < start) should raise ValueError."""
        seg = Segment(
            minified_start=10,
            minified_end=5,
            original_start=0,
            original_end=10,
        )
        with pytest.raises(ValueError, match="invalid minified range"):
            SourceMap(segments=[seg])

    def test_invalid_original_range_raises_error(self) -> None:
        """Invalid original range (end < start) should raise ValueError."""
        seg = Segment(
            minified_start=0,
            minified_end=10,
            original_start=10,
            original_end=5,
        )
        with pytest.raises(ValueError, match="invalid original range"):
            SourceMap(segments=[seg])


class TestAddSegment:
    """Tests for add_segment method."""

    def test_add_to_empty_map(self) -> None:
        """Adding to empty map should work."""
        sm = SourceMap()
        seg = Segment(
            minified_start=0, minified_end=10, original_start=0, original_end=10
        )
        sm.add_segment(seg)
        assert len(sm) == 1
        assert sm.segments[0] == seg

    def test_add_after_existing(self) -> None:
        """Adding segment after existing should work."""
        sm = SourceMap(
            [
                Segment(
                    minified_start=0, minified_end=10, original_start=0, original_end=10
                )
            ]
        )
        seg = Segment(
            minified_start=10, minified_end=20, original_start=20, original_end=30
        )
        sm.add_segment(seg)
        assert len(sm) == 2
        assert sm.segments[1] == seg

    def test_add_before_existing(self) -> None:
        """Adding segment before existing should insert at correct position."""
        sm = SourceMap(
            [
                Segment(
                    minified_start=10,
                    minified_end=20,
                    original_start=20,
                    original_end=30,
                )
            ]
        )
        seg = Segment(
            minified_start=0, minified_end=10, original_start=0, original_end=10
        )
        sm.add_segment(seg)
        assert len(sm) == 2
        assert sm.segments[0] == seg

    def test_add_between_existing(self) -> None:
        """Adding segment between existing should insert at correct position."""
        sm = SourceMap(
            [
                Segment(
                    minified_start=0, minified_end=10, original_start=0, original_end=10
                ),
                Segment(
                    minified_start=30,
                    minified_end=40,
                    original_start=50,
                    original_end=60,
                ),
            ]
        )
        seg = Segment(
            minified_start=15, minified_end=25, original_start=25, original_end=35
        )
        sm.add_segment(seg)
        assert len(sm) == 3
        assert sm.segments[1] == seg

    def test_add_overlapping_with_previous_raises_error(self) -> None:
        """Adding segment overlapping with previous should raise error."""
        sm = SourceMap(
            [
                Segment(
                    minified_start=0, minified_end=15, original_start=0, original_end=15
                )
            ]
        )
        seg = Segment(
            minified_start=10, minified_end=20, original_start=20, original_end=30
        )
        with pytest.raises(ValueError, match="overlaps with previous"):
            sm.add_segment(seg)

    def test_add_overlapping_with_next_raises_error(self) -> None:
        """Adding segment overlapping with next should raise error."""
        sm = SourceMap(
            [
                Segment(
                    minified_start=10,
                    minified_end=20,
                    original_start=20,
                    original_end=30,
                )
            ]
        )
        seg = Segment(
            minified_start=0, minified_end=15, original_start=0, original_end=15
        )
        with pytest.raises(ValueError, match="overlaps with next"):
            sm.add_segment(seg)


class TestMinifiedToOriginal:
    """Tests for minified_to_original method."""

    def test_empty_map_returns_none(self) -> None:
        """Empty source map should return None."""
        sm = SourceMap()
        assert sm.minified_to_original(5) is None

    def test_negative_offset_returns_none(self) -> None:
        """Negative offset should return None."""
        sm = SourceMap(
            [
                Segment(
                    minified_start=0, minified_end=10, original_start=0, original_end=10
                )
            ]
        )
        assert sm.minified_to_original(-1) is None

    def test_offset_before_first_segment_returns_none(self) -> None:
        """Offset before first segment should return None."""
        sm = SourceMap(
            [
                Segment(
                    minified_start=5,
                    minified_end=15,
                    original_start=10,
                    original_end=20,
                )
            ]
        )
        assert sm.minified_to_original(0) is None
        assert sm.minified_to_original(4) is None

    def test_offset_at_segment_start(self) -> None:
        """Offset at segment start should map correctly."""
        sm = SourceMap(
            [
                Segment(
                    minified_start=0,
                    minified_end=10,
                    original_start=100,
                    original_end=110,
                )
            ]
        )
        assert sm.minified_to_original(0) == 100

    def test_offset_at_segment_end_minus_one(self) -> None:
        """Offset at segment end - 1 should map correctly."""
        sm = SourceMap(
            [
                Segment(
                    minified_start=0,
                    minified_end=10,
                    original_start=100,
                    original_end=110,
                )
            ]
        )
        # Last valid offset is 9 (end is exclusive)
        assert sm.minified_to_original(9) == 109

    def test_offset_at_segment_end_returns_none(self) -> None:
        """Offset exactly at segment end should return None (gap)."""
        sm = SourceMap(
            [
                Segment(
                    minified_start=0,
                    minified_end=10,
                    original_start=100,
                    original_end=110,
                )
            ]
        )
        # Offset 10 is not in the segment [0, 10)
        assert sm.minified_to_original(10) is None

    def test_offset_in_gap_returns_none(self) -> None:
        """Offset in gap between segments should return None."""
        sm = SourceMap(
            [
                Segment(
                    minified_start=0, minified_end=10, original_start=0, original_end=10
                ),
                Segment(
                    minified_start=20,
                    minified_end=30,
                    original_start=100,
                    original_end=110,
                ),
            ]
        )
        # Gap is [10, 20)
        assert sm.minified_to_original(10) is None
        assert sm.minified_to_original(15) is None
        assert sm.minified_to_original(19) is None

    def test_offset_after_gap_maps_correctly(self) -> None:
        """Offset at start of segment after gap should map correctly."""
        sm = SourceMap(
            [
                Segment(
                    minified_start=0, minified_end=10, original_start=0, original_end=10
                ),
                Segment(
                    minified_start=20,
                    minified_end=30,
                    original_start=100,
                    original_end=110,
                ),
            ]
        )
        assert sm.minified_to_original(20) == 100
        assert sm.minified_to_original(25) == 105

    def test_identity_mapping(self) -> None:
        """Identity mapping (same length) should work correctly."""
        sm = SourceMap(
            [
                Segment(
                    minified_start=0,
                    minified_end=100,
                    original_start=0,
                    original_end=100,
                )
            ]
        )
        for offset in [0, 1, 50, 99]:
            assert sm.minified_to_original(offset) == offset

    def test_offset_mapping_with_different_lengths(self) -> None:
        """Mapping with different segment lengths."""
        # Segment maps minified [0, 10) to original [0, 10)
        sm = SourceMap(
            [
                Segment(
                    minified_start=0, minified_end=10, original_start=0, original_end=10
                )
            ]
        )
        assert sm.minified_to_original(5) == 5

    def test_multiple_segments_sequential_lookup(self) -> None:
        """Test lookup across multiple segments."""
        sm = SourceMap(
            [
                Segment(
                    minified_start=0, minified_end=10, original_start=0, original_end=10
                ),
                Segment(
                    minified_start=10,
                    minified_end=20,
                    original_start=50,
                    original_end=60,
                ),
                Segment(
                    minified_start=20,
                    minified_end=30,
                    original_start=100,
                    original_end=110,
                ),
            ]
        )
        # First segment
        assert sm.minified_to_original(0) == 0
        assert sm.minified_to_original(9) == 9
        # Second segment
        assert sm.minified_to_original(10) == 50
        assert sm.minified_to_original(19) == 59
        # Third segment
        assert sm.minified_to_original(20) == 100
        assert sm.minified_to_original(29) == 109


class TestOriginalToMinified:
    """Tests for original_to_minified method."""

    def test_empty_map_returns_none(self) -> None:
        """Empty source map should return None."""
        sm = SourceMap()
        assert sm.original_to_minified(5) is None

    def test_negative_offset_returns_none(self) -> None:
        """Negative offset should return None."""
        sm = SourceMap(
            [
                Segment(
                    minified_start=0, minified_end=10, original_start=0, original_end=10
                )
            ]
        )
        assert sm.original_to_minified(-1) is None

    def test_offset_before_first_segment_returns_none(self) -> None:
        """Offset before first segment should return None."""
        sm = SourceMap(
            [
                Segment(
                    minified_start=5,
                    minified_end=15,
                    original_start=10,
                    original_end=20,
                )
            ]
        )
        assert sm.original_to_minified(0) is None
        assert sm.original_to_minified(9) is None

    def test_offset_at_segment_start(self) -> None:
        """Offset at segment start should map correctly."""
        sm = SourceMap(
            [
                Segment(
                    minified_start=100,
                    minified_end=110,
                    original_start=0,
                    original_end=10,
                )
            ]
        )
        assert sm.original_to_minified(0) == 100

    def test_offset_at_segment_end_minus_one(self) -> None:
        """Offset at segment end - 1 should map correctly."""
        sm = SourceMap(
            [
                Segment(
                    minified_start=100,
                    minified_end=110,
                    original_start=0,
                    original_end=10,
                )
            ]
        )
        assert sm.original_to_minified(9) == 109

    def test_offset_at_segment_end_returns_none(self) -> None:
        """Offset exactly at segment end should return None (removed code)."""
        sm = SourceMap(
            [
                Segment(
                    minified_start=100,
                    minified_end=110,
                    original_start=0,
                    original_end=10,
                )
            ]
        )
        assert sm.original_to_minified(10) is None

    def test_offset_in_removed_code_returns_none(self) -> None:
        """Offset in removed code (gap in original) should return None."""
        # This represents: original [0,10) kept, [10,100) removed, [100,110) kept
        sm = SourceMap(
            [
                Segment(
                    minified_start=0, minified_end=10, original_start=0, original_end=10
                ),
                Segment(
                    minified_start=10,
                    minified_end=20,
                    original_start=100,
                    original_end=110,
                ),
            ]
        )
        # Offsets 10-99 in original were removed
        assert sm.original_to_minified(10) is None
        assert sm.original_to_minified(50) is None
        assert sm.original_to_minified(99) is None

    def test_offset_after_removed_code_maps_correctly(self) -> None:
        """Offset in segment after removed code should map correctly."""
        sm = SourceMap(
            [
                Segment(
                    minified_start=0, minified_end=10, original_start=0, original_end=10
                ),
                Segment(
                    minified_start=10,
                    minified_end=20,
                    original_start=100,
                    original_end=110,
                ),
            ]
        )
        assert sm.original_to_minified(100) == 10
        assert sm.original_to_minified(105) == 15


class TestBidirectionalConsistency:
    """Tests for bidirectional mapping consistency."""

    def test_roundtrip_minified_original_minified(self) -> None:
        """Minified -> Original -> Minified should be identity for valid offsets."""
        sm = SourceMap(
            [
                Segment(
                    minified_start=0, minified_end=10, original_start=0, original_end=10
                ),
                Segment(
                    minified_start=10,
                    minified_end=20,
                    original_start=50,
                    original_end=60,
                ),
            ]
        )
        for minified_offset in range(20):
            original = sm.minified_to_original(minified_offset)
            if original is not None:
                back = sm.original_to_minified(original)
                assert (
                    back == minified_offset
                ), f"Roundtrip failed for minified offset {minified_offset}"

    def test_roundtrip_original_minified_original(self) -> None:
        """Original -> Minified -> Original should be identity for valid offsets."""
        sm = SourceMap(
            [
                Segment(
                    minified_start=0, minified_end=10, original_start=0, original_end=10
                ),
                Segment(
                    minified_start=10,
                    minified_end=20,
                    original_start=50,
                    original_end=60,
                ),
            ]
        )
        # Test offsets that are in segments
        valid_original_offsets = list(range(10)) + list(range(50, 60))
        for original_offset in valid_original_offsets:
            minified = sm.original_to_minified(original_offset)
            if minified is not None:
                back = sm.minified_to_original(minified)
                assert (
                    back == original_offset
                ), f"Roundtrip failed for original offset {original_offset}"


class TestFindSegment:
    """Tests for find_segment methods."""

    def test_find_segment_containing_minified_empty_map(self) -> None:
        """Empty map should return None."""
        sm = SourceMap()
        assert sm.find_segment_containing_minified(5) is None

    def test_find_segment_containing_minified_negative(self) -> None:
        """Negative offset should return None."""
        sm = SourceMap(
            [
                Segment(
                    minified_start=0, minified_end=10, original_start=0, original_end=10
                )
            ]
        )
        assert sm.find_segment_containing_minified(-1) is None

    def test_find_segment_containing_minified_valid(self) -> None:
        """Valid offset should return correct segment."""
        seg = Segment(
            minified_start=0, minified_end=10, original_start=0, original_end=10
        )
        sm = SourceMap([seg])
        assert sm.find_segment_containing_minified(5) == seg

    def test_find_segment_containing_minified_in_gap(self) -> None:
        """Offset in gap should return None."""
        sm = SourceMap(
            [
                Segment(
                    minified_start=0, minified_end=10, original_start=0, original_end=10
                ),
                Segment(
                    minified_start=20,
                    minified_end=30,
                    original_start=50,
                    original_end=60,
                ),
            ]
        )
        assert sm.find_segment_containing_minified(15) is None

    def test_find_segment_containing_original_valid(self) -> None:
        """Valid original offset should return correct segment."""
        seg = Segment(
            minified_start=0, minified_end=10, original_start=100, original_end=110
        )
        sm = SourceMap([seg])
        assert sm.find_segment_containing_original(105) == seg

    def test_find_segment_containing_original_in_removed(self) -> None:
        """Original offset in removed code should return None."""
        sm = SourceMap(
            [
                Segment(
                    minified_start=0, minified_end=10, original_start=0, original_end=10
                ),
                Segment(
                    minified_start=10,
                    minified_end=20,
                    original_start=100,
                    original_end=110,
                ),
            ]
        )
        assert sm.find_segment_containing_original(50) is None


class TestRangeQueries:
    """Tests for range query methods."""

    def test_get_minified_range_empty(self) -> None:
        """Empty map should return None."""
        sm = SourceMap()
        assert sm.get_minified_range() is None

    def test_get_minified_range_single_segment(self) -> None:
        """Single segment range."""
        sm = SourceMap(
            [
                Segment(
                    minified_start=10,
                    minified_end=20,
                    original_start=0,
                    original_end=10,
                )
            ]
        )
        assert sm.get_minified_range() == (10, 20)

    def test_get_minified_range_multiple_segments(self) -> None:
        """Multiple segments range."""
        sm = SourceMap(
            [
                Segment(
                    minified_start=0, minified_end=10, original_start=0, original_end=10
                ),
                Segment(
                    minified_start=20,
                    minified_end=30,
                    original_start=50,
                    original_end=60,
                ),
            ]
        )
        assert sm.get_minified_range() == (0, 30)

    def test_get_original_range_empty(self) -> None:
        """Empty map should return None."""
        sm = SourceMap()
        assert sm.get_original_range() is None

    def test_get_original_range_single_segment(self) -> None:
        """Single segment range."""
        sm = SourceMap(
            [
                Segment(
                    minified_start=0,
                    minified_end=10,
                    original_start=100,
                    original_end=110,
                )
            ]
        )
        assert sm.get_original_range() == (100, 110)

    def test_get_original_range_multiple_segments(self) -> None:
        """Multiple segments range (reports min start and max end)."""
        sm = SourceMap(
            [
                Segment(
                    minified_start=0,
                    minified_end=10,
                    original_start=50,
                    original_end=60,
                ),
                Segment(
                    minified_start=10,
                    minified_end=20,
                    original_start=0,
                    original_end=10,
                ),
                Segment(
                    minified_start=20,
                    minified_end=30,
                    original_start=100,
                    original_end=110,
                ),
            ]
        )
        assert sm.get_original_range() == (0, 110)


class TestBoundaryConditions:
    """Critical boundary condition tests."""

    def test_zero_length_minified_segment(self) -> None:
        """Zero-length minified segment (insertion marker)."""
        sm = SourceMap(
            [
                Segment(
                    minified_start=5, minified_end=5, original_start=0, original_end=10
                )
            ]
        )
        # Zero-length segments don't contain any offset
        assert sm.minified_to_original(5) is None

    def test_zero_length_original_segment(self) -> None:
        """Zero-length original segment (deletion marker)."""
        sm = SourceMap(
            [
                Segment(
                    minified_start=0, minified_end=10, original_start=5, original_end=5
                )
            ]
        )
        # Any offset in minified maps to the single point in original
        assert sm.minified_to_original(0) == 5
        assert (
            sm.minified_to_original(5) == 10
        )  # offset within maps to original_start + offset

    def test_adjacent_segments_no_gap(self) -> None:
        """Adjacent segments with no gap should both be accessible."""
        sm = SourceMap(
            [
                Segment(
                    minified_start=0, minified_end=10, original_start=0, original_end=10
                ),
                Segment(
                    minified_start=10,
                    minified_end=20,
                    original_start=10,
                    original_end=20,
                ),
            ]
        )
        # End of first segment
        assert sm.minified_to_original(9) == 9
        # Start of second segment (exactly at boundary)
        assert sm.minified_to_original(10) == 10

    def test_single_char_segment(self) -> None:
        """Single character segment (length 1)."""
        sm = SourceMap(
            [
                Segment(
                    minified_start=5,
                    minified_end=6,
                    original_start=100,
                    original_end=101,
                )
            ]
        )
        assert sm.minified_to_original(4) is None
        assert sm.minified_to_original(5) == 100
        assert sm.minified_to_original(6) is None

    def test_very_large_offsets(self) -> None:
        """Test with very large offset values."""
        large = 1_000_000_000
        sm = SourceMap(
            [
                Segment(
                    minified_start=large,
                    minified_end=large + 100,
                    original_start=large * 2,
                    original_end=large * 2 + 100,
                )
            ]
        )
        assert sm.minified_to_original(large) == large * 2
        assert sm.minified_to_original(large + 50) == large * 2 + 50
        assert sm.minified_to_original(large - 1) is None

    def test_contiguous_segments_cover_full_range(self) -> None:
        """Contiguous segments should cover full range without gaps."""
        sm = SourceMap(
            [
                Segment(
                    minified_start=0, minified_end=10, original_start=0, original_end=10
                ),
                Segment(
                    minified_start=10,
                    minified_end=20,
                    original_start=10,
                    original_end=20,
                ),
                Segment(
                    minified_start=20,
                    minified_end=30,
                    original_start=20,
                    original_end=30,
                ),
            ]
        )
        # Every offset from 0 to 29 should map successfully
        for i in range(30):
            result = sm.minified_to_original(i)
            assert result is not None, f"Offset {i} should not be in a gap"
            assert result == i, f"Identity mapping expected for offset {i}"

    def test_off_by_one_at_segment_boundaries(self) -> None:
        """Critical off-by-one test at segment boundaries."""
        sm = SourceMap(
            [
                Segment(
                    minified_start=0,
                    minified_end=10,
                    original_start=100,
                    original_end=110,
                ),
                Segment(
                    minified_start=15,
                    minified_end=25,
                    original_start=200,
                    original_end=210,
                ),
            ]
        )

        # First segment boundaries
        assert sm.minified_to_original(0) == 100  # First valid
        assert sm.minified_to_original(9) == 109  # Last valid in first segment
        assert sm.minified_to_original(10) is None  # First gap offset

        # Gap
        assert sm.minified_to_original(14) is None  # Last gap offset

        # Second segment boundaries
        assert sm.minified_to_original(15) == 200  # First valid in second segment
        assert sm.minified_to_original(24) == 209  # Last valid
        assert sm.minified_to_original(25) is None  # After last segment


class TestRepr:
    """Tests for string representation."""

    def test_repr_empty(self) -> None:
        """Empty source map repr."""
        sm = SourceMap()
        assert repr(sm) == "SourceMap(segments=0)"

    def test_repr_with_segments(self) -> None:
        """Source map with segments repr."""
        sm = SourceMap(
            [
                Segment(
                    minified_start=0, minified_end=10, original_start=0, original_end=10
                ),
                Segment(
                    minified_start=10,
                    minified_end=20,
                    original_start=10,
                    original_end=20,
                ),
            ]
        )
        assert repr(sm) == "SourceMap(segments=2)"
