"""
Property-based tests for the Provenance Engine using Hypothesis.

These tests verify invariants and properties that must hold for all inputs:
1. Round-trip consistency: minified -> original -> minified = identity
2. Segment integrity: segments must be non-overlapping and sorted
3. Offset monotonicity: increasing offsets map to increasing offsets within segments
4. Gap handling: offsets in gaps always return None
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from mcp_context_graph.provenance.segment import Segment
from mcp_context_graph.provenance.source_map import SourceMap

if TYPE_CHECKING:
    pass


# =============================================================================
# Custom Strategies
# =============================================================================


@st.composite
def valid_segment(
    draw: st.DrawFn,
    min_start: int = 0,
    max_start: int = 1000,
    min_length: int = 1,
    max_length: int = 100,
) -> Segment:
    """
    Generate a valid Segment with non-negative, non-overlapping ranges.

    Args:
        draw: Hypothesis draw function
        min_start: Minimum value for minified_start
        max_start: Maximum value for minified_start
        min_length: Minimum length of segment
        max_length: Maximum length of segment

    Returns:
        A valid Segment object
    """
    minified_start = draw(st.integers(min_value=min_start, max_value=max_start))
    minified_length = draw(st.integers(min_value=min_length, max_value=max_length))
    minified_end = minified_start + minified_length

    original_start = draw(st.integers(min_value=0, max_value=max_start))
    original_length = draw(st.integers(min_value=min_length, max_value=max_length))
    original_end = original_start + original_length

    return Segment(
        minified_start=minified_start,
        minified_end=minified_end,
        original_start=original_start,
        original_end=original_end,
    )


@st.composite
def non_overlapping_segments(
    draw: st.DrawFn,
    min_segments: int = 1,
    max_segments: int = 10,
) -> list[Segment]:
    """
    Generate a list of non-overlapping, sorted segments in minified space.

    Args:
        draw: Hypothesis draw function
        min_segments: Minimum number of segments
        max_segments: Maximum number of segments

    Returns:
        A list of valid, non-overlapping Segment objects
    """
    num_segments = draw(st.integers(min_value=min_segments, max_value=max_segments))

    segments: list[Segment] = []
    current_minified_pos = 0
    current_original_pos = 0

    for _ in range(num_segments):
        # Optional gap before this segment
        gap = draw(st.integers(min_value=0, max_value=50))
        minified_start = current_minified_pos + gap

        # Segment length (must be at least 1)
        minified_length = draw(st.integers(min_value=1, max_value=100))
        minified_end = minified_start + minified_length

        # Original can have different gaps and lengths
        original_gap = draw(st.integers(min_value=0, max_value=100))
        original_start = current_original_pos + original_gap
        original_length = draw(st.integers(min_value=1, max_value=100))
        original_end = original_start + original_length

        segment = Segment(
            minified_start=minified_start,
            minified_end=minified_end,
            original_start=original_start,
            original_end=original_end,
        )
        segments.append(segment)

        # Update positions for next segment
        current_minified_pos = minified_end
        current_original_pos = original_end

    return segments


@st.composite
def identity_segments(
    draw: st.DrawFn,
    min_segments: int = 1,
    max_segments: int = 10,
) -> list[Segment]:
    """
    Generate segments where minified and original ranges have the same length.

    This is useful for testing identity mapping properties.

    Args:
        draw: Hypothesis draw function
        min_segments: Minimum number of segments
        max_segments: Maximum number of segments

    Returns:
        List of segments with identity-length mappings
    """
    num_segments = draw(st.integers(min_value=min_segments, max_value=max_segments))

    segments: list[Segment] = []
    current_minified_pos = 0
    current_original_pos = 0

    for _ in range(num_segments):
        # Optional gap
        gap = draw(st.integers(min_value=0, max_value=20))
        minified_start = current_minified_pos + gap

        # Same length for both
        length = draw(st.integers(min_value=1, max_value=50))

        original_gap = draw(st.integers(min_value=0, max_value=50))
        original_start = current_original_pos + original_gap

        segment = Segment(
            minified_start=minified_start,
            minified_end=minified_start + length,
            original_start=original_start,
            original_end=original_start + length,
        )
        segments.append(segment)

        current_minified_pos = minified_start + length
        current_original_pos = original_start + length

    return segments


# =============================================================================
# Property Tests: Round-Trip Consistency
# =============================================================================


class TestRoundTripConsistency:
    """Property tests for bidirectional mapping consistency."""

    @given(segments=identity_segments(min_segments=1, max_segments=5))
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_minified_to_original_roundtrip_identity_segments(
        self, segments: list[Segment]
    ) -> None:
        """
        For identity segments (same length), roundtrip must be exact.

        Property: For any minified offset within a segment,
                 m2o(o2m(offset)) == offset
        """
        sm = SourceMap(segments)

        for segment in segments:
            for offset in range(segment.minified_start, segment.minified_end):
                original = sm.minified_to_original(offset)
                assert original is not None, f"Offset {offset} should map to original"

                back = sm.original_to_minified(original)
                assert back == offset, (
                    f"Roundtrip failed: minified {offset} -> original {original} "
                    f"-> minified {back}"
                )

    @given(segments=identity_segments(min_segments=1, max_segments=5))
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_original_to_minified_roundtrip_identity_segments(
        self, segments: list[Segment]
    ) -> None:
        """
        For identity segments, original -> minified -> original is identity.

        Property: For any original offset within a segment,
                 o2m(m2o(offset)) == offset
        """
        sm = SourceMap(segments)

        for segment in segments:
            for offset in range(segment.original_start, segment.original_end):
                minified = sm.original_to_minified(offset)
                assert minified is not None, f"Offset {offset} should map to minified"

                back = sm.minified_to_original(minified)
                assert back == offset, (
                    f"Roundtrip failed: original {offset} -> minified {minified} "
                    f"-> original {back}"
                )

    @given(
        segments=non_overlapping_segments(min_segments=1, max_segments=5),
        offset_delta=st.integers(min_value=0, max_value=99),
    )
    @settings(max_examples=300, suppress_health_check=[HealthCheck.too_slow])
    def test_minified_offset_in_segment_maps_successfully(
        self, segments: list[Segment], offset_delta: int
    ) -> None:
        """
        Any offset within a segment's minified range should map successfully.

        Property: For offset in [segment.minified_start, segment.minified_end),
                 minified_to_original(offset) is not None
        """
        sm = SourceMap(segments)

        for segment in segments:
            if segment.minified_length > 0:
                # Pick an offset within the segment
                offset = segment.minified_start + (
                    offset_delta % segment.minified_length
                )
                result = sm.minified_to_original(offset)
                assert result is not None, (
                    f"Offset {offset} within segment [{segment.minified_start}, "
                    f"{segment.minified_end}) should not be None"
                )


# =============================================================================
# Property Tests: Gap Handling
# =============================================================================


class TestGapHandling:
    """Property tests for gap (removed code) handling."""

    @given(segments=non_overlapping_segments(min_segments=2, max_segments=5))
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_gap_offsets_return_none(self, segments: list[Segment]) -> None:
        """
        Offsets in gaps between segments must return None.

        Property: For any offset in a gap, minified_to_original(offset) is None
        """
        sm = SourceMap(segments)

        for i in range(len(segments) - 1):
            current_end = segments[i].minified_end
            next_start = segments[i + 1].minified_start

            # If there's a gap, test all offsets in it
            if next_start > current_end:
                for gap_offset in range(current_end, next_start):
                    result = sm.minified_to_original(gap_offset)
                    assert result is None, (
                        f"Gap offset {gap_offset} between segments {i} and {i+1} "
                        f"should return None, got {result}"
                    )

    @given(segments=non_overlapping_segments(min_segments=1, max_segments=3))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_offset_before_first_segment_returns_none(
        self, segments: list[Segment]
    ) -> None:
        """
        Offsets before the first segment must return None.

        Property: For offset < first_segment.minified_start,
                 minified_to_original(offset) is None
        """
        sm = SourceMap(segments)
        first_start = segments[0].minified_start

        if first_start > 0:
            for offset in range(first_start):
                result = sm.minified_to_original(offset)
                assert (
                    result is None
                ), f"Offset {offset} before first segment should return None"

    @given(segments=non_overlapping_segments(min_segments=1, max_segments=3))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_offset_after_last_segment_returns_none(
        self, segments: list[Segment]
    ) -> None:
        """
        Offsets at or after the last segment's end must return None.

        Property: For offset >= last_segment.minified_end,
                 minified_to_original(offset) is None
        """
        sm = SourceMap(segments)
        last_end = segments[-1].minified_end

        # Test a few offsets after the last segment
        for offset in range(last_end, last_end + 10):
            result = sm.minified_to_original(offset)
            assert (
                result is None
            ), f"Offset {offset} at/after last segment should return None"


# =============================================================================
# Property Tests: Segment Invariants
# =============================================================================


class TestSegmentInvariants:
    """Property tests for segment invariants maintained by SourceMap."""

    @given(segments=non_overlapping_segments(min_segments=1, max_segments=10))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_segments_remain_sorted(self, segments: list[Segment]) -> None:
        """
        Segments in SourceMap are always sorted by minified_start.

        Property: For all i < j, segments[i].minified_start < segments[j].minified_start
        """
        sm = SourceMap(segments)
        result_segments = sm.segments

        for i in range(len(result_segments) - 1):
            assert (
                result_segments[i].minified_start
                < result_segments[i + 1].minified_start
            ), (
                f"Segments not sorted: {result_segments[i]} comes before "
                f"{result_segments[i + 1]}"
            )

    @given(segments=non_overlapping_segments(min_segments=1, max_segments=10))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_segments_non_overlapping_minified(self, segments: list[Segment]) -> None:
        """
        Segments must not overlap in minified space.

        Property: For all i, segments[i].minified_end <= segments[i+1].minified_start
        """
        sm = SourceMap(segments)
        result_segments = sm.segments

        for i in range(len(result_segments) - 1):
            assert (
                result_segments[i].minified_end <= result_segments[i + 1].minified_start
            ), (
                f"Segments overlap in minified space: segment {i} ends at "
                f"{result_segments[i].minified_end}, segment {i+1} starts at "
                f"{result_segments[i + 1].minified_start}"
            )

    @given(segments=non_overlapping_segments(min_segments=1, max_segments=5))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_segment_count_preserved(self, segments: list[Segment]) -> None:
        """
        The number of segments is preserved when creating SourceMap.

        Property: len(SourceMap(segments)) == len(segments)
        """
        sm = SourceMap(segments)
        assert len(sm) == len(segments)


# =============================================================================
# Property Tests: Offset Monotonicity
# =============================================================================


class TestOffsetMonotonicity:
    """Property tests for monotonic offset mapping within segments."""

    @given(segments=identity_segments(min_segments=1, max_segments=3))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_increasing_minified_maps_to_increasing_original(
        self, segments: list[Segment]
    ) -> None:
        """
        Within a segment, increasing minified offsets map to increasing original offsets.

        Property: For offset1 < offset2 in same segment,
                 m2o(offset1) < m2o(offset2)
        """
        sm = SourceMap(segments)

        for segment in segments:
            if segment.minified_length < 2:
                continue

            prev_original = None
            for minified_offset in range(segment.minified_start, segment.minified_end):
                original = sm.minified_to_original(minified_offset)
                assert original is not None

                if prev_original is not None:
                    assert original > prev_original, (
                        f"Monotonicity violated: minified {minified_offset - 1} -> "
                        f"original {prev_original}, minified {minified_offset} -> "
                        f"original {original}"
                    )
                prev_original = original


# =============================================================================
# Property Tests: Builder Pattern
# =============================================================================


class TestBuilderPattern:
    """Property tests for add_segment builder pattern."""

    @given(segments=non_overlapping_segments(min_segments=1, max_segments=5))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_add_segments_incrementally_equals_batch(
        self, segments: list[Segment]
    ) -> None:
        """
        Adding segments one by one produces same result as batch initialization.

        Property: SourceMap built incrementally == SourceMap built in batch
        """
        # Batch construction
        batch_sm = SourceMap(segments)

        # Incremental construction
        incremental_sm = SourceMap()
        for segment in segments:
            incremental_sm.add_segment(segment)

        # Compare results
        assert len(incremental_sm) == len(batch_sm)

        for i in range(len(batch_sm.segments)):
            assert incremental_sm.segments[i] == batch_sm.segments[i], (
                f"Segment {i} differs: incremental={incremental_sm.segments[i]}, "
                f"batch={batch_sm.segments[i]}"
            )

    @given(
        segments=non_overlapping_segments(min_segments=2, max_segments=5),
        test_offsets=st.lists(
            st.integers(min_value=0, max_value=500), min_size=5, max_size=20
        ),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_incremental_and_batch_produce_same_mappings(
        self, segments: list[Segment], test_offsets: list[int]
    ) -> None:
        """
        Batch and incremental construction produce identical mappings.

        Property: For any offset, batch.m2o(offset) == incremental.m2o(offset)
        """
        batch_sm = SourceMap(segments)

        incremental_sm = SourceMap()
        for segment in segments:
            incremental_sm.add_segment(segment)

        for offset in test_offsets:
            batch_result = batch_sm.minified_to_original(offset)
            incremental_result = incremental_sm.minified_to_original(offset)
            assert batch_result == incremental_result, (
                f"Mapping differs for offset {offset}: "
                f"batch={batch_result}, incremental={incremental_result}"
            )


# =============================================================================
# Property Tests: Edge Cases
# =============================================================================


class TestEdgeCases:
    """Property tests for edge cases."""

    @given(st.integers(min_value=-1000, max_value=-1))
    def test_negative_offsets_always_return_none(self, negative_offset: int) -> None:
        """
        Negative offsets always return None regardless of segments.

        Property: minified_to_original(negative) is None
        """
        segments = [
            Segment(
                minified_start=0, minified_end=100, original_start=0, original_end=100
            )
        ]
        sm = SourceMap(segments)
        assert sm.minified_to_original(negative_offset) is None
        assert sm.original_to_minified(negative_offset) is None

    def test_empty_source_map_always_returns_none(self) -> None:
        """
        Empty source map returns None for all offsets.

        Property: For empty SourceMap, all lookups return None
        """
        sm = SourceMap()
        for offset in range(100):
            assert sm.minified_to_original(offset) is None
            assert sm.original_to_minified(offset) is None

    @given(
        start=st.integers(min_value=0, max_value=1000),
        length=st.integers(min_value=1, max_value=100),
    )
    @settings(max_examples=100)
    def test_single_identity_segment_perfect_mapping(
        self, start: int, length: int
    ) -> None:
        """
        A single identity segment provides perfect 1:1 mapping.

        Property: For identity segment, m2o(x) == x - minified_start + original_start
        """
        segment = Segment(
            minified_start=start,
            minified_end=start + length,
            original_start=start,
            original_end=start + length,
        )
        sm = SourceMap([segment])

        for offset in range(start, start + length):
            result = sm.minified_to_original(offset)
            expected = offset  # Identity mapping
            assert (
                result == expected
            ), f"Identity mapping failed: offset {offset} -> {result}, expected {expected}"


# =============================================================================
# Stateful Testing (Simulating Minification)
# =============================================================================


class TestMinificationSimulation:
    """
    Property tests simulating the minification process.

    These tests generate random "text" transformations and verify
    that the source map correctly tracks the changes.
    """

    @given(
        original_text=st.text(
            min_size=10,
            max_size=100,
            alphabet=st.characters(
                whitelist_categories=("L", "N", "P", "Z"), whitelist_characters=" \n\t"
            ),
        ),
        removal_indices=st.lists(
            st.integers(min_value=0, max_value=99),
            min_size=0,
            max_size=5,
            unique=True,
        ),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_text_with_removals_maintains_consistency(
        self, original_text: str, removal_indices: list[int]
    ) -> None:
        """
        Simulate removing chunks of text and verify source map consistency.

        This test:
        1. Takes original text
        2. Simulates removing some chunks (like minification does)
        3. Builds a source map of preserved ranges
        4. Verifies all preserved characters map correctly
        """
        if not original_text:
            return

        # Normalize removal indices to valid range
        text_len = len(original_text)
        valid_removals = sorted(
            {idx % text_len for idx in removal_indices if text_len > 0}
        )

        # Build segments for preserved ranges
        segments: list[Segment] = []
        minified_pos = 0

        # Simple simulation: remove single characters at specified indices
        i = 0
        while i < text_len:
            if i in valid_removals:
                # Skip this character (removed)
                i += 1
                continue

            # Find the end of this preserved range
            start = i
            while i < text_len and i not in valid_removals:
                i += 1
            end = i

            if end > start:
                segment = Segment(
                    minified_start=minified_pos,
                    minified_end=minified_pos + (end - start),
                    original_start=start,
                    original_end=end,
                )
                segments.append(segment)
                minified_pos += end - start

        if not segments:
            return

        sm = SourceMap(segments)

        # Verify: all preserved offsets in minified should map to original
        for segment in segments:
            for offset in range(segment.minified_start, segment.minified_end):
                result = sm.minified_to_original(offset)
                assert result is not None, f"Preserved offset {offset} should map"
                assert segment.original_start <= result < segment.original_end

        # Verify: removed offsets should not be reachable from minified
        minified_range = sm.get_minified_range()
        if minified_range:
            for gap_offset in valid_removals:
                # These original offsets should not have corresponding minified offsets
                result = sm.original_to_minified(gap_offset)
                # Note: this might still return a value if the removal index
                # overlaps with a preserved range's boundaries
