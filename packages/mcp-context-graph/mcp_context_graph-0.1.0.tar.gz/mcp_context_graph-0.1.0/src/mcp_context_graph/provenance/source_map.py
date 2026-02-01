"""
SourceMap: Source map with bisect-based O(log n) offset lookup.

This module provides efficient bidirectional mapping between
minified and original source positions using binary search.

The SourceMap maintains a list of Segments that map ranges in minified
text to ranges in original text. Gaps between segments represent code
that was removed during minification.
"""

from __future__ import annotations

import bisect
import logging
from typing import TYPE_CHECKING

from mcp_context_graph.provenance.segment import Segment

if TYPE_CHECKING:
    from collections.abc import Sequence

logger = logging.getLogger(__name__)


class SourceMap:
    """
    Bidirectional source map using binary search for O(log n) lookups.

    The SourceMap stores segments that map ranges in minified text to
    corresponding ranges in original text. Each segment represents a
    contiguous block of text that was preserved during minification.

    Segments must be:
    - Non-overlapping in both minified and original space
    - Sorted by minified_start (ascending)
    - Contiguous or separated by gaps (representing removed code)

    Example:
        Original: "def foo():\n    return 42\n"
        Minified: "def foo(): ..."

        Segment 1: minified=[0,10) -> original=[0,10)  (signature)
        Segment 2: minified=[11,14) -> original=[11,25) (body -> ellipsis)
        Gap at minified offset 10 represents newline/body removal.
    """

    __slots__ = ("_segments", "_minified_starts", "_original_starts")

    def __init__(self, segments: Sequence[Segment] | None = None) -> None:
        """
        Initialize a SourceMap with optional segments.

        Args:
            segments: Sequence of Segment objects. Must be sorted by
                     minified_start and non-overlapping. If None, creates
                     an empty source map.

        Raises:
            ValueError: If segments are overlapping or not sorted.
        """
        self._segments: list[Segment] = []
        self._minified_starts: list[int] = []
        self._original_starts: list[int] = []

        if segments:
            self._validate_and_set_segments(list(segments))

    def _validate_and_set_segments(self, segments: list[Segment]) -> None:
        """
        Validate segments are sorted and non-overlapping, then store them.

        Args:
            segments: List of segments to validate and store.

        Raises:
            ValueError: If segments are invalid.
        """
        if not segments:
            return

        # Sort by minified_start to ensure correct order
        sorted_segments = sorted(segments, key=lambda s: s.minified_start)

        # Validate non-overlapping in minified space
        for i in range(1, len(sorted_segments)):
            prev = sorted_segments[i - 1]
            curr = sorted_segments[i]

            if prev.minified_end > curr.minified_start:
                msg = (
                    f"Overlapping segments in minified space: "
                    f"segment {i-1} ends at {prev.minified_end}, "
                    f"segment {i} starts at {curr.minified_start}"
                )
                raise ValueError(msg)

        # Validate non-negative ranges
        for i, seg in enumerate(sorted_segments):
            if seg.minified_start < 0 or seg.original_start < 0:
                msg = f"Segment {i} has negative offset"
                raise ValueError(msg)
            if seg.minified_end < seg.minified_start:
                msg = f"Segment {i} has invalid minified range"
                raise ValueError(msg)
            if seg.original_end < seg.original_start:
                msg = f"Segment {i} has invalid original range"
                raise ValueError(msg)

        self._segments = sorted_segments
        self._minified_starts = [s.minified_start for s in sorted_segments]
        self._original_starts = [s.original_start for s in sorted_segments]

        logger.debug(
            "SourceMap initialized with %d segments",
            len(self._segments),
        )

    @property
    def segments(self) -> tuple[Segment, ...]:
        """Return immutable tuple of segments."""
        return tuple(self._segments)

    def __len__(self) -> int:
        """Return number of segments."""
        return len(self._segments)

    def __bool__(self) -> bool:
        """Return True if source map has segments."""
        return bool(self._segments)

    def add_segment(self, segment: Segment) -> None:
        """
        Add a segment to the source map.

        The segment must not overlap with existing segments in minified space.

        Args:
            segment: The segment to add.

        Raises:
            ValueError: If segment overlaps with existing segments.
        """
        if not self._segments:
            self._segments = [segment]
            self._minified_starts = [segment.minified_start]
            self._original_starts = [segment.original_start]
            return

        # Find insertion point using bisect
        idx = bisect.bisect_left(self._minified_starts, segment.minified_start)

        # Check overlap with previous segment
        if idx > 0:
            prev = self._segments[idx - 1]
            if prev.minified_end > segment.minified_start:
                msg = (
                    f"Segment overlaps with previous: "
                    f"prev ends at {prev.minified_end}, "
                    f"new starts at {segment.minified_start}"
                )
                raise ValueError(msg)

        # Check overlap with next segment
        if idx < len(self._segments):
            next_seg = self._segments[idx]
            if segment.minified_end > next_seg.minified_start:
                msg = (
                    f"Segment overlaps with next: "
                    f"new ends at {segment.minified_end}, "
                    f"next starts at {next_seg.minified_start}"
                )
                raise ValueError(msg)

        # Insert at correct position
        self._segments.insert(idx, segment)
        self._minified_starts.insert(idx, segment.minified_start)
        self._original_starts.insert(idx, segment.original_start)

    def minified_to_original(self, minified_offset: int) -> int | None:
        """
        Map a minified offset to the corresponding original offset.

        Uses binary search for O(log n) lookup.

        Args:
            minified_offset: Byte offset in the minified text.

        Returns:
            The corresponding byte offset in the original text,
            or None if the offset falls in a gap (removed code).
        """
        if not self._segments:
            logger.debug("minified_to_original: empty source map")
            return None

        if minified_offset < 0:
            logger.debug("minified_to_original: negative offset %d", minified_offset)
            return None

        # Find the rightmost segment whose minified_start <= minified_offset
        # bisect_right gives us the insertion point, so we need idx - 1
        idx = bisect.bisect_right(self._minified_starts, minified_offset) - 1

        if idx < 0:
            # Offset is before the first segment
            logger.debug(
                "minified_to_original: offset %d before first segment",
                minified_offset,
            )
            return None

        segment = self._segments[idx]

        # Check if offset is within this segment's minified range
        # Note: We use < for end boundary (half-open interval [start, end))
        if minified_offset >= segment.minified_end:
            # Offset is in a gap between segments
            logger.debug(
                "minified_to_original: offset %d in gap after segment %d",
                minified_offset,
                idx,
            )
            return None

        # Calculate the offset within the segment
        offset_within_segment = minified_offset - segment.minified_start

        # Map to original space
        # For identity segments (same length), this is straightforward
        # For non-identity segments, we scale proportionally
        if segment.minified_length == segment.original_length:
            # Identity mapping - most common case
            original_offset = segment.original_start + offset_within_segment
        elif segment.minified_length == 0:
            # Zero-length segment (insertion point)
            original_offset = segment.original_start
        else:
            # Non-identity mapping - return the start of original range
            # This handles cases like "..." replacing a function body
            # Any offset within the minified replacement maps to original start
            original_offset = segment.original_start + offset_within_segment

        logger.debug(
            "minified_to_original: %d -> %d (segment %d)",
            minified_offset,
            original_offset,
            idx,
        )

        return original_offset

    def original_to_minified(self, original_offset: int) -> int | None:
        """
        Map an original offset to the corresponding minified offset.

        Uses binary search for O(log n) lookup.

        Args:
            original_offset: Byte offset in the original text.

        Returns:
            The corresponding byte offset in the minified text,
            or None if the offset falls in removed code.
        """
        if not self._segments:
            logger.debug("original_to_minified: empty source map")
            return None

        if original_offset < 0:
            logger.debug("original_to_minified: negative offset %d", original_offset)
            return None

        # Find the rightmost segment whose original_start <= original_offset
        idx = bisect.bisect_right(self._original_starts, original_offset) - 1

        if idx < 0:
            # Offset is before the first segment
            logger.debug(
                "original_to_minified: offset %d before first segment",
                original_offset,
            )
            return None

        segment = self._segments[idx]

        # Check if offset is within this segment's original range
        if original_offset >= segment.original_end:
            # Offset is in removed code (gap in original that maps to nothing)
            logger.debug(
                "original_to_minified: offset %d in removed code after segment %d",
                original_offset,
                idx,
            )
            return None

        # Calculate the offset within the segment
        offset_within_segment = original_offset - segment.original_start

        # Map to minified space
        if segment.minified_length == segment.original_length:
            # Identity mapping
            minified_offset = segment.minified_start + offset_within_segment
        elif segment.original_length == 0:
            # Zero-length original segment
            minified_offset = segment.minified_start
        else:
            # Non-identity mapping - proportional scaling
            minified_offset = segment.minified_start + offset_within_segment

        logger.debug(
            "original_to_minified: %d -> %d (segment %d)",
            original_offset,
            minified_offset,
            idx,
        )

        return minified_offset

    def find_segment_containing_minified(self, minified_offset: int) -> Segment | None:
        """
        Find the segment that contains the given minified offset.

        Args:
            minified_offset: Byte offset in minified text.

        Returns:
            The Segment containing this offset, or None if in a gap.
        """
        if not self._segments or minified_offset < 0:
            return None

        idx = bisect.bisect_right(self._minified_starts, minified_offset) - 1
        if idx < 0:
            return None

        segment = self._segments[idx]
        if minified_offset < segment.minified_end:
            return segment
        return None

    def find_segment_containing_original(self, original_offset: int) -> Segment | None:
        """
        Find the segment that contains the given original offset.

        Args:
            original_offset: Byte offset in original text.

        Returns:
            The Segment containing this offset, or None if in removed code.
        """
        if not self._segments or original_offset < 0:
            return None

        idx = bisect.bisect_right(self._original_starts, original_offset) - 1
        if idx < 0:
            return None

        segment = self._segments[idx]
        if original_offset < segment.original_end:
            return segment
        return None

    def get_minified_range(self) -> tuple[int, int] | None:
        """
        Get the total range covered in minified space.

        Returns:
            Tuple of (start, end) offsets, or None if empty.
        """
        if not self._segments:
            return None
        return (
            self._segments[0].minified_start,
            self._segments[-1].minified_end,
        )

    def get_original_range(self) -> tuple[int, int] | None:
        """
        Get the total range covered in original space.

        Returns:
            Tuple of (min_start, max_end) offsets, or None if empty.
        """
        if not self._segments:
            return None
        min_start = min(s.original_start for s in self._segments)
        max_end = max(s.original_end for s in self._segments)
        return (min_start, max_end)

    def __repr__(self) -> str:
        """Return string representation."""
        return f"SourceMap(segments={len(self._segments)})"
