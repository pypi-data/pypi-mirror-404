"""
Provenance module for source maps and offset tracking.

Contains:
- Segment: Pydantic V2 model for source map segments
- SourceMap: Source map with bisect-based offset lookup
- IntervalTree: Helper for interval queries
"""

from mcp_context_graph.provenance.segment import Segment
from mcp_context_graph.provenance.source_map import SourceMap

__all__ = ["Segment", "SourceMap"]
