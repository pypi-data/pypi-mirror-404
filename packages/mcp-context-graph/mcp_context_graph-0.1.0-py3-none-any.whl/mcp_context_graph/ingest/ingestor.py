"""
Ingestor: Orchestrator for file ingestion.

This module coordinates the full ingestion pipeline:
1. Discover files respecting .gitignore and hardcoded exclusions
2. Parse files using TreeSitterParser
3. Normalize AST captures to GenericNodes
4. Minify and generate source maps
5. Build the context graph

Safety Features:
- Parses .gitignore using pathspec library
- Hardcoded exclusions for node_modules, .git, __pycache__, .venv
- Generator-based file walking to avoid loading disk into RAM
- Graceful error handling - parse failures don't crash ingestion
"""

from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING

import pathspec

from mcp_context_graph.core.edge import EdgeType, GraphEdge
from mcp_context_graph.core.graph import ContextGraph
from mcp_context_graph.core.node import GraphNode, NodeType, SourceLocation
from mcp_context_graph.ingest.minifier import Minifier
from mcp_context_graph.ingest.normalizer import Normalizer
from mcp_context_graph.ingest.tree_sitter_parser import TreeSitterParser
from mcp_context_graph.provenance.segment import Segment
from mcp_context_graph.provenance.source_map import SourceMap

if TYPE_CHECKING:
    from collections.abc import Generator

logger = logging.getLogger(__name__)


# Hardcoded exclusions - these will ALWAYS be excluded to prevent crashes
DEFAULT_EXCLUSIONS: frozenset[str] = frozenset(
    {
        "node_modules",
        "__pycache__",
        ".git",
        ".venv",
        ".env",
        "venv",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "dist",
        "build",
        ".tox",
        ".nox",
        ".eggs",
        "*.egg-info",
        ".coverage",
        "htmlcov",
        ".hypothesis",
    }
)

# Supported file extensions and their languages
LANGUAGE_EXTENSIONS: dict[str, str] = {
    ".py": "python",
    ".pyw": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
}


class ProvenanceTracker:
    """
    Centralized store for SourceMap objects.

    GraphNodes only store source_map_id (string), and this tracker
    maintains the actual SourceMap instances for later lookup.
    """

    __slots__ = ("_store",)

    def __init__(self) -> None:
        """Initialize an empty provenance store."""
        self._store: dict[str, SourceMap] = {}

    def register(self, source_map: SourceMap, file_path: str) -> str:
        """
        Register a SourceMap and return its unique ID.

        Args:
            source_map: The SourceMap to register.
            file_path: Path to the source file (used for ID generation).

        Returns:
            Unique source_map_id string.
        """
        # Generate deterministic ID based on file path and content hash
        content_hash = hashlib.sha256(
            f"{file_path}:{len(source_map)}".encode()
        ).hexdigest()[:12]
        source_map_id = f"map_{content_hash}"

        self._store[source_map_id] = source_map
        logger.debug("Registered source map: %s for %s", source_map_id, file_path)
        return source_map_id

    def get(self, source_map_id: str) -> SourceMap | None:
        """
        Get a SourceMap by its ID.

        Args:
            source_map_id: The ID returned from register().

        Returns:
            The SourceMap if found, None otherwise.
        """
        return self._store.get(source_map_id)

    def minified_to_original(
        self,
        source_map_id: str,
        offset: int,
    ) -> int | None:
        """
        Map a minified offset to original offset.

        Args:
            source_map_id: The source map ID.
            offset: The minified byte offset.

        Returns:
            Original byte offset, or None if mapping fails.
        """
        source_map = self.get(source_map_id)
        if source_map:
            return source_map.minified_to_original(offset)
        return None

    def original_to_minified(
        self,
        source_map_id: str,
        offset: int,
    ) -> int | None:
        """
        Map an original offset to minified offset.

        Args:
            source_map_id: The source map ID.
            offset: The original byte offset.

        Returns:
            Minified byte offset, or None if mapping fails.
        """
        source_map = self.get(source_map_id)
        if source_map:
            return source_map.original_to_minified(offset)
        return None

    def __len__(self) -> int:
        """Return number of registered source maps."""
        return len(self._store)

    def clear(self) -> None:
        """Clear all registered source maps."""
        self._store.clear()


class IngestorStats:
    """Statistics collected during ingestion."""

    __slots__ = (
        "files_discovered",
        "files_processed",
        "files_skipped",
        "files_failed",
        "nodes_created",
        "edges_created",
    )

    def __init__(self) -> None:
        """Initialize all counters to zero."""
        self.files_discovered: int = 0
        self.files_processed: int = 0
        self.files_skipped: int = 0
        self.files_failed: int = 0
        self.nodes_created: int = 0
        self.edges_created: int = 0

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"IngestorStats(discovered={self.files_discovered}, "
            f"processed={self.files_processed}, skipped={self.files_skipped}, "
            f"failed={self.files_failed}, nodes={self.nodes_created}, "
            f"edges={self.edges_created})"
        )


class Ingestor:
    """
    Orchestrator for the ingestion pipeline.

    The Ingestor walks a project directory, parses source files,
    builds a ContextGraph, and maintains provenance via SourceMaps.

    Features:
    - Respects .gitignore patterns using pathspec
    - Hardcoded exclusions prevent crashes (node_modules, .git, etc.)
    - Generator-based file walking for memory efficiency
    - Graceful error handling - one bad file doesn't crash everything
    - Supports Python, TypeScript, and JavaScript

    Example:
        ingestor = Ingestor(Path("/path/to/project"))
        graph, tracker, stats = ingestor.ingest()
        print(f"Ingested {stats.files_processed} files")
    """

    __slots__ = (
        "_project_root",
        "_gitignore_spec",
        "_graph",
        "_tracker",
        "_minifier",
        "_stats",
        "_file_timestamps",
    )

    def __init__(self, project_root: Path | str) -> None:
        """
        Initialize the Ingestor for a project.

        Args:
            project_root: Path to the project root directory.

        Raises:
            ValueError: If project_root doesn't exist or isn't a directory.
        """
        self._project_root = Path(project_root).resolve()

        if not self._project_root.exists():
            msg = f"Project root does not exist: {self._project_root}"
            raise ValueError(msg)

        if not self._project_root.is_dir():
            msg = f"Project root is not a directory: {self._project_root}"
            raise ValueError(msg)

        self._gitignore_spec = self._load_gitignore()
        self._graph = ContextGraph()
        self._tracker = ProvenanceTracker()
        self._minifier = Minifier()
        self._stats = IngestorStats()
        # Track file modification timestamps for lazy re-ingestion
        self._file_timestamps: dict[str, float] = {}

        logger.debug("Ingestor initialized for: %s", self._project_root)

    @property
    def project_root(self) -> Path:
        """Return the project root path."""
        return self._project_root

    @property
    def graph(self) -> ContextGraph:
        """Return the constructed ContextGraph."""
        return self._graph

    @property
    def tracker(self) -> ProvenanceTracker:
        """Return the ProvenanceTracker."""
        return self._tracker

    @property
    def stats(self) -> IngestorStats:
        """Return ingestion statistics."""
        return self._stats

    def _load_gitignore(self) -> pathspec.PathSpec:
        """
        Load .gitignore patterns from the project root.

        Returns:
            PathSpec configured with gitignore patterns.
        """
        gitignore_path = self._project_root / ".gitignore"
        patterns: list[str] = []

        if gitignore_path.exists():
            try:
                content = gitignore_path.read_text(encoding="utf-8")
                patterns = content.splitlines()
                logger.debug(
                    "Loaded %d patterns from .gitignore",
                    len([p for p in patterns if p and not p.startswith("#")]),
                )
            except OSError as e:
                logger.warning("Failed to read .gitignore: %s", e)

        return pathspec.PathSpec.from_lines("gitignore", patterns)

    def _should_exclude(self, path: Path) -> bool:
        """
        Check if a path should be excluded from ingestion.

        Checks both hardcoded exclusions and .gitignore patterns.

        Args:
            path: The path to check (relative to project root).

        Returns:
            True if the path should be excluded.
        """
        # Check hardcoded exclusions first (fastest check)
        for part in path.parts:
            if part in DEFAULT_EXCLUSIONS:
                return True
            # Handle glob patterns like *.egg-info
            for pattern in DEFAULT_EXCLUSIONS:
                if "*" in pattern:
                    import fnmatch

                    if fnmatch.fnmatch(part, pattern):
                        return True

        # Check .gitignore patterns
        try:
            relative_path = str(path.relative_to(self._project_root))
        except ValueError:
            relative_path = str(path)

        return self._gitignore_spec.match_file(relative_path)

    def _detect_language(self, file_path: Path) -> str | None:
        """
        Detect the programming language from file extension.

        Args:
            file_path: Path to the source file.

        Returns:
            Language name ("python", "typescript", "javascript") or None.
        """
        suffix = file_path.suffix.lower()
        return LANGUAGE_EXTENSIONS.get(suffix)

    def _walk_files(self) -> Generator[Path, None, None]:
        """
        Generator that walks the project directory yielding source files.

        Uses os.walk for efficient directory traversal and filters
        based on exclusions and supported file types.

        Yields:
            Path objects for each source file to process.
        """
        for root, dirs, files in os.walk(self._project_root):
            root_path = Path(root)

            # In-place filter to prevent descent into excluded directories
            # This is critical for performance - we never even enter node_modules
            dirs[:] = [d for d in dirs if not self._should_exclude(root_path / d)]

            for filename in files:
                file_path = root_path / filename
                self._stats.files_discovered += 1

                # Check if file is excluded
                if self._should_exclude(file_path):
                    self._stats.files_skipped += 1
                    continue

                # Check if language is supported
                language = self._detect_language(file_path)
                if language is None:
                    self._stats.files_skipped += 1
                    continue

                yield file_path

    def _generate_node_id(self, file_path: Path, name: str, node_type: str) -> str:
        """
        Generate a unique node ID.

        Args:
            file_path: Path to the source file.
            name: Name of the symbol.
            node_type: Type of the node.

        Returns:
            Unique string ID.
        """
        relative_path = file_path.relative_to(self._project_root)
        content = f"{relative_path}:{name}:{node_type}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _process_file(self, file_path: Path) -> bool:
        """
        Process a single source file.

        This is where the magic happens:
        1. Read the file
        2. Detect language
        3. Parse with tree-sitter (TODO: when implemented)
        4. Create module node
        5. Create function/class nodes with minification
        6. Register source maps

        For now, we create a simple module node for each file
        until tree-sitter parsing is implemented.

        Args:
            file_path: Path to the source file.

        Returns:
            True if processing succeeded, False otherwise.
        """
        logger.info("Ingesting file: %s", file_path)

        try:
            # Read file content
            content = file_path.read_text(encoding="utf-8")
            language = self._detect_language(file_path)

            if language is None:
                return False

            # Calculate relative path for qualified names
            relative_path = str(file_path.relative_to(self._project_root))

            # Create module node for the file
            module_id = self._generate_node_id(file_path, relative_path, "module")
            module_location = SourceLocation(
                file_path=relative_path,
                start_byte=0,
                end_byte=len(content.encode("utf-8")),
                start_line=1,
                start_column=0,
                end_line=content.count("\n") + 1,
                end_column=0,
            )

            # Create identity minification for the module (preserves full content)
            minification = self._minifier.minify_text(content)
            source_map_id = self._tracker.register(
                minification.source_map, relative_path
            )

            module_node = GraphNode(
                id=module_id,
                type=NodeType.MODULE,
                name=file_path.stem,
                qualified_name=relative_path,
                language=language,
                signature=f"# {file_path.name}",  # Brief signature
                location=module_location,
                source_map_id=source_map_id,
            )

            self._graph.add_node(module_node)
            self._stats.nodes_created += 1

            # Parse the file with TreeSitterParser and extract definitions
            self._extract_definitions_with_tree_sitter(
                content, file_path, relative_path, language, module_id
            )

            # Record file timestamp for lazy re-ingestion tracking
            self._file_timestamps[relative_path] = os.path.getmtime(file_path)

            return True

        except OSError as e:
            logger.warning("Failed to read %s: %s", file_path, e)
            return False
        except UnicodeDecodeError as e:
            logger.warning("Encoding error in %s: %s", file_path, e)
            return False
        except Exception as e:
            # Catch-all to prevent one bad file from crashing everything
            logger.exception("Failed to process %s: %s", file_path, e)
            return False

    def _extract_definitions_with_tree_sitter(
        self,
        content: str,
        file_path: Path,
        relative_path: str,
        language: str,
        module_id: str,
    ) -> None:
        """
        Extract definitions using tree-sitter parser and normalizer.

        This method orchestrates the full parsing pipeline:
        1. Parse with TreeSitterParser
        2. Normalize to GenericNodes
        3. Minify and generate source maps
        4. Add GraphNodes to the graph

        Falls back to simple regex extraction if tree-sitter parsing fails.

        Args:
            content: File content as string.
            file_path: Path to the file.
            relative_path: Relative path from project root.
            language: Programming language.
            module_id: ID of the parent module node.
        """
        try:
            parser = TreeSitterParser()
            normalizer = Normalizer()

            # Try to parse with tree-sitter
            parse_result = parser.parse_string(content, language, file_path)

            if parse_result is None:
                # Tree-sitter parsing failed, fall back to simple extraction
                logger.debug(
                    "Tree-sitter parsing failed for %s, using fallback", relative_path
                )
                self._extract_simple_definitions(
                    content, file_path, relative_path, language, module_id
                )
                return
        except Exception as e:
            # Any tree-sitter error, fall back to simple extraction
            logger.debug(
                "Tree-sitter error for %s: %s, using fallback", relative_path, e
            )
            self._extract_simple_definitions(
                content, file_path, relative_path, language, module_id
            )
            return

        # Normalize the parse result to generic nodes
        normalized = normalizer.normalize(parse_result)

        # Process all definitions (functions, classes, methods)
        for generic_node in normalized.all_definitions:
            # Update file path in location
            location = SourceLocation(
                file_path=relative_path,
                start_byte=generic_node.location.start_byte,
                end_byte=generic_node.location.end_byte,
                start_line=generic_node.location.start_line,
                start_column=generic_node.location.start_column,
                end_line=generic_node.location.end_line,
                end_column=generic_node.location.end_column,
            )

            # Minify the definition (extract signature only)
            minification = self._minifier.minify_function(
                text=content,
                signature_end=generic_node.signature_end,
                body_start=generic_node.body_start,
                body_end=generic_node.body_end,
            )
            source_map_id = self._tracker.register(
                minification.source_map, f"{relative_path}:{generic_node.name}"
            )

            # Generate node ID
            node_id = self._generate_node_id(
                file_path, generic_node.qualified_name, generic_node.type.value
            )

            # Create the graph node
            node = GraphNode(
                id=node_id,
                type=generic_node.type,
                name=generic_node.name,
                qualified_name=f"{relative_path}:{generic_node.qualified_name}",
                language=language,
                signature=minification.minified_text,
                location=location,
                source_map_id=source_map_id,
            )

            try:
                self._graph.add_node(node)
                self._stats.nodes_created += 1

                # Create CONTAINS edge from module to definition
                edge = GraphEdge(
                    source_id=module_id,
                    target_id=node_id,
                    type=EdgeType.CONTAINS,
                    location=location,
                )
                self._graph.add_edge(edge)
                self._stats.edges_created += 1

            except ValueError as e:
                # Node might already exist if there's duplicate names
                logger.debug("Skipping duplicate node %s: %s", generic_node.name, e)

        logger.debug(
            "Extracted %d definitions from %s using tree-sitter",
            len(normalized.all_definitions),
            relative_path,
        )

    def _extract_simple_definitions(
        self,
        content: str,
        file_path: Path,
        relative_path: str,
        language: str,
        module_id: str,
    ) -> None:
        """
        Simple definition extraction without tree-sitter (fallback).

        This is a fallback implementation that uses basic regex-based
        extraction when tree-sitter parsing fails.

        Args:
            content: File content as string.
            file_path: Path to the file.
            relative_path: Relative path from project root.
            language: Programming language.
            module_id: ID of the parent module node.
        """
        import re

        lines = content.split("\n")

        if language == "python":
            # Match Python function and class definitions
            func_pattern = re.compile(r"^\s*def\s+(\w+)\s*\(")
            class_pattern = re.compile(r"^\s*class\s+(\w+)\s*[:\(]")
        else:
            # Match TypeScript/JavaScript function and class definitions
            func_pattern = re.compile(
                r"^\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\("
            )
            class_pattern = re.compile(r"^\s*(?:export\s+)?class\s+(\w+)")

        byte_offset = 0

        for line_num, line in enumerate(lines, start=1):
            line_bytes = line.encode("utf-8")

            # Check for function definition
            func_match = func_pattern.match(line)
            if func_match:
                name = func_match.group(1)
                self._create_definition_node(
                    name=name,
                    node_type=NodeType.FUNCTION,
                    file_path=file_path,
                    relative_path=relative_path,
                    language=language,
                    module_id=module_id,
                    line_num=line_num,
                    start_byte=byte_offset,
                    end_byte=byte_offset + len(line_bytes),
                    line=line,
                )

            # Check for class definition
            class_match = class_pattern.match(line)
            if class_match:
                name = class_match.group(1)
                self._create_definition_node(
                    name=name,
                    node_type=NodeType.CLASS,
                    file_path=file_path,
                    relative_path=relative_path,
                    language=language,
                    module_id=module_id,
                    line_num=line_num,
                    start_byte=byte_offset,
                    end_byte=byte_offset + len(line_bytes),
                    line=line,
                )

            byte_offset += len(line_bytes) + 1  # +1 for newline

    def _create_definition_node(
        self,
        name: str,
        node_type: NodeType,
        file_path: Path,
        relative_path: str,
        language: str,
        module_id: str,
        line_num: int,
        start_byte: int,
        end_byte: int,
        line: str,
    ) -> None:
        """
        Create a node for a function or class definition.

        Args:
            name: Symbol name.
            node_type: NodeType.FUNCTION or NodeType.CLASS.
            file_path: Full path to file.
            relative_path: Path relative to project root.
            language: Programming language.
            module_id: Parent module node ID.
            line_num: Line number of definition.
            start_byte: Start byte offset.
            end_byte: End byte offset.
            line: The source line.
        """
        node_id = self._generate_node_id(file_path, name, node_type.value)
        qualified_name = f"{relative_path}:{name}"

        location = SourceLocation(
            file_path=relative_path,
            start_byte=start_byte,
            end_byte=end_byte,
            start_line=line_num,
            start_column=0,
            end_line=line_num,
            end_column=len(line),
        )

        # Create simple identity source map for the signature line
        segment = Segment(
            minified_start=0,
            minified_end=len(line.encode("utf-8")),
            original_start=start_byte,
            original_end=end_byte,
        )
        source_map = SourceMap([segment])
        source_map_id = self._tracker.register(source_map, f"{relative_path}:{name}")

        node = GraphNode(
            id=node_id,
            type=node_type,
            name=name,
            qualified_name=qualified_name,
            language=language,
            signature=line.strip(),
            location=location,
            source_map_id=source_map_id,
        )

        try:
            self._graph.add_node(node)
            self._stats.nodes_created += 1

            # Create CONTAINS edge from module to definition
            edge = GraphEdge(
                source_id=module_id,
                target_id=node_id,
                type=EdgeType.CONTAINS,
                location=location,
            )
            self._graph.add_edge(edge)
            self._stats.edges_created += 1

        except ValueError as e:
            # Node might already exist if there's duplicate names
            logger.debug("Skipping duplicate node %s: %s", name, e)

    def ingest(self) -> tuple[ContextGraph, ProvenanceTracker, IngestorStats]:
        """
        Run the full ingestion pipeline.

        Walks the project directory, processes each source file,
        builds the graph, and returns the results.

        Returns:
            Tuple of (ContextGraph, ProvenanceTracker, IngestorStats).
        """
        logger.info("Starting ingestion of: %s", self._project_root)

        for file_path in self._walk_files():
            success = self._process_file(file_path)
            if success:
                self._stats.files_processed += 1
            else:
                self._stats.files_failed += 1

        logger.info("Ingestion complete: %s", self._stats)

        return self._graph, self._tracker, self._stats

    def ingest_file(self, file_path: Path | str) -> bool:
        """
        Ingest a single file.

        Useful for incremental updates or testing.

        Args:
            file_path: Path to the file to ingest.

        Returns:
            True if ingestion succeeded.
        """
        file_path = Path(file_path).resolve()

        if not file_path.exists():
            logger.warning("File does not exist: %s", file_path)
            return False

        self._stats.files_discovered += 1
        success = self._process_file(file_path)

        if success:
            self._stats.files_processed += 1
        else:
            self._stats.files_failed += 1

        return success

    def refresh_changed_files(self) -> list[str]:
        """
        Detect and re-ingest files that have been modified since initial ingestion.

        This method implements lazy re-ingestion (Check-on-Read) capability:
        1. Iterates through all tracked files
        2. Checks current modification timestamps vs stored timestamps
        3. For modified files: removes old nodes from graph, re-processes file
        4. For deleted files: removes from graph and stops tracking

        This operation is synchronous and designed to be fast. It does NOT
        implement a background watcher - it must be called explicitly by
        MCP tools when needed.

        Returns:
            List of relative file paths that were refreshed (modified or deleted).

        Example:
            ingestor = Ingestor(Path("/project"))
            ingestor.ingest()
            # ... user modifies some files ...
            refreshed = ingestor.refresh_changed_files()
            print(f"Refreshed {len(refreshed)} files")
        """
        refreshed_files: list[str] = []

        # Iterate over a copy of keys since we may modify the dict
        tracked_files = list(self._file_timestamps.keys())

        for relative_path in tracked_files:
            full_path = self._project_root / relative_path

            # Check if file was deleted
            if not full_path.exists():
                logger.info("Detected deletion: %s", relative_path)

                # Remove nodes from graph
                self._graph.remove_nodes_by_file(relative_path)

                # Stop tracking this file
                del self._file_timestamps[relative_path]

                refreshed_files.append(relative_path)
                continue

            # Check if file was modified
            try:
                current_mtime = os.path.getmtime(full_path)
            except OSError as e:
                logger.warning("Failed to stat %s: %s", relative_path, e)
                continue

            stored_mtime = self._file_timestamps[relative_path]

            if current_mtime > stored_mtime:
                logger.info("Detected change in %s", relative_path)

                # Remove old nodes from graph
                removed_count = self._graph.remove_nodes_by_file(relative_path)
                logger.debug(
                    "Removed %d old nodes for %s", removed_count, relative_path
                )

                # Re-process the file (parse -> minify -> add to graph)
                success = self._process_file(full_path)

                if success:
                    refreshed_files.append(relative_path)
                    logger.debug("Successfully re-ingested %s", relative_path)
                else:
                    # If re-processing failed, remove from tracking
                    # to avoid repeated failures
                    logger.warning("Failed to re-ingest %s", relative_path)
                    del self._file_timestamps[relative_path]

        if refreshed_files:
            logger.info(
                "Refreshed %d file(s): %s", len(refreshed_files), refreshed_files
            )

        return refreshed_files

    def __repr__(self) -> str:
        """Return string representation."""
        return f"Ingestor(root={self._project_root}, stats={self._stats})"
