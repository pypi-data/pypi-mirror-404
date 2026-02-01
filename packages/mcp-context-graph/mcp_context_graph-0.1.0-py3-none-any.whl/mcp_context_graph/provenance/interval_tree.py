"""
IntervalTree: Interval-based lookup data structure.

This module provides an interval tree implementation for efficient
range queries. While the SourceMap uses bisect-based lookup for
simplicity, this module provides a more general solution for
complex interval operations.

Note: For ASCII source maps with non-overlapping segments,
the bisect-based approach in SourceMap is sufficient and faster.
This module is provided for potential future extensions.
"""

from __future__ import annotations

import bisect
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Interval[T]:
    """
    An interval with associated data.

    Attributes:
        start: Start of the interval (inclusive).
        end: End of the interval (exclusive).
        data: Associated data for this interval.
    """

    start: int
    end: int
    data: T

    @property
    def length(self) -> int:
        """Return the length of the interval."""
        return self.end - self.start

    def contains(self, point: int) -> bool:
        """Check if a point is within this interval."""
        return self.start <= point < self.end

    def overlaps(self, other: Interval[T]) -> bool:
        """Check if this interval overlaps with another."""
        return self.start < other.end and other.start < self.end

    def __lt__(self, other: Interval[T]) -> bool:
        """Compare by start position."""
        return self.start < other.start


class IntervalTree[T]:
    """
    A simple interval tree for non-overlapping intervals.

    This implementation is optimized for non-overlapping intervals
    sorted by start position, which is the case for source map segments.

    For overlapping intervals, consider using a more sophisticated
    implementation like intervaltree library.

    Example:
        tree = IntervalTree[str]()
        tree.add(Interval(0, 10, "first"))
        tree.add(Interval(10, 20, "second"))

        result = tree.find(5)  # Returns "first"
        result = tree.find(15)  # Returns "second"
    """

    __slots__ = ("_intervals", "_starts")

    def __init__(self) -> None:
        """Initialize an empty interval tree."""
        self._intervals: list[Interval[T]] = []
        self._starts: list[int] = []

    def add(self, interval: Interval[T]) -> None:
        """
        Add an interval to the tree.

        Args:
            interval: The interval to add.

        Raises:
            ValueError: If interval overlaps with existing intervals.
        """
        if not self._intervals:
            self._intervals.append(interval)
            self._starts.append(interval.start)
            return

        # Find insertion point
        idx = bisect.bisect_left(self._starts, interval.start)

        # Check for overlap with neighboring intervals
        if idx > 0:
            prev = self._intervals[idx - 1]
            if prev.end > interval.start:
                msg = f"Interval overlaps with previous: {prev} vs {interval}"
                raise ValueError(msg)

        if idx < len(self._intervals):
            next_int = self._intervals[idx]
            if interval.end > next_int.start:
                msg = f"Interval overlaps with next: {interval} vs {next_int}"
                raise ValueError(msg)

        # Insert in sorted order
        self._intervals.insert(idx, interval)
        self._starts.insert(idx, interval.start)

    def find(self, point: int) -> T | None:
        """
        Find the data associated with the interval containing a point.

        Uses binary search for O(log n) lookup.

        Args:
            point: The point to query.

        Returns:
            The data associated with the containing interval,
            or None if the point is not in any interval.
        """
        if not self._intervals:
            return None

        # Find rightmost interval whose start <= point
        idx = bisect.bisect_right(self._starts, point) - 1

        if idx < 0:
            return None

        interval = self._intervals[idx]
        if interval.contains(point):
            return interval.data

        return None

    def find_interval(self, point: int) -> Interval[T] | None:
        """
        Find the interval containing a point.

        Args:
            point: The point to query.

        Returns:
            The Interval containing the point, or None.
        """
        if not self._intervals:
            return None

        idx = bisect.bisect_right(self._starts, point) - 1

        if idx < 0:
            return None

        interval = self._intervals[idx]
        if interval.contains(point):
            return interval

        return None

    def find_overlapping(self, start: int, end: int) -> list[Interval[T]]:
        """
        Find all intervals that overlap with a range.

        Args:
            start: Start of the query range.
            end: End of the query range.

        Returns:
            List of overlapping intervals.
        """
        if not self._intervals:
            return []

        results: list[Interval[T]] = []

        # Find first potentially overlapping interval
        idx = bisect.bisect_right(self._starts, start) - 1
        idx = max(0, idx)

        # Check intervals until we're past the range
        while idx < len(self._intervals):
            interval = self._intervals[idx]

            if interval.start >= end:
                break

            if interval.end > start:
                results.append(interval)

            idx += 1

        return results

    def all_intervals(self) -> list[Interval[T]]:
        """Return all intervals in sorted order."""
        return list(self._intervals)

    def clear(self) -> None:
        """Remove all intervals."""
        self._intervals.clear()
        self._starts.clear()

    def __len__(self) -> int:
        """Return number of intervals."""
        return len(self._intervals)

    def __bool__(self) -> bool:
        """Return True if tree has intervals."""
        return bool(self._intervals)

    def __contains__(self, point: int) -> bool:
        """Check if a point is in any interval."""
        return self.find(point) is not None

    def __repr__(self) -> str:
        """Return string representation."""
        return f"IntervalTree(intervals={len(self._intervals)})"
