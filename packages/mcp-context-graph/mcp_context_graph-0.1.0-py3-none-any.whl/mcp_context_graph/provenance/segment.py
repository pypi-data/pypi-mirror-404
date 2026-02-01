"""
Segment Pydantic V2 model for source map segments.

A segment maps a range in minified text to a range in original text.
"""

from pydantic import BaseModel, ConfigDict


class Segment(BaseModel):
    """
    A segment in a source map that maps minified offsets to original offsets.

    Attributes:
        minified_start: Start byte offset in minified text
        minified_end: End byte offset in minified text
        original_start: Start byte offset in original text
        original_end: End byte offset in original text
    """

    minified_start: int
    minified_end: int
    original_start: int
    original_end: int

    model_config = ConfigDict(frozen=True)

    @property
    def minified_length(self) -> int:
        """Length of the segment in minified text."""
        return self.minified_end - self.minified_start

    @property
    def original_length(self) -> int:
        """Length of the segment in original text."""
        return self.original_end - self.original_start
