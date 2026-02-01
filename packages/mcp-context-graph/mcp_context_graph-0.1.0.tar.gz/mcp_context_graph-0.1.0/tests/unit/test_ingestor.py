"""Unit tests for the Ingestor module."""

from pathlib import Path

import pytest

from mcp_context_graph.core.node import NodeType
from mcp_context_graph.ingest.ingestor import (
    DEFAULT_EXCLUSIONS,
    LANGUAGE_EXTENSIONS,
    Ingestor,
    IngestorStats,
    ProvenanceTracker,
)
from mcp_context_graph.provenance.segment import Segment
from mcp_context_graph.provenance.source_map import SourceMap


class TestProvenanceTracker:
    """Tests for ProvenanceTracker."""

    def test_init_empty(self):
        """Test creating an empty tracker."""
        tracker = ProvenanceTracker()
        assert len(tracker) == 0

    def test_register_source_map(self):
        """Test registering a source map."""
        tracker = ProvenanceTracker()
        segment = Segment(
            minified_start=0,
            minified_end=10,
            original_start=0,
            original_end=10,
        )
        source_map = SourceMap([segment])

        map_id = tracker.register(source_map, "test.py")
        assert map_id.startswith("map_")
        assert len(tracker) == 1

    def test_get_source_map(self):
        """Test retrieving a source map by ID."""
        tracker = ProvenanceTracker()
        segment = Segment(
            minified_start=0,
            minified_end=10,
            original_start=0,
            original_end=10,
        )
        source_map = SourceMap([segment])

        map_id = tracker.register(source_map, "test.py")
        retrieved = tracker.get(map_id)

        assert retrieved is not None
        assert len(retrieved) == 1

    def test_get_source_map_not_found(self):
        """Test getting non-existent source map returns None."""
        tracker = ProvenanceTracker()
        assert tracker.get("nonexistent") is None

    def test_minified_to_original(self):
        """Test minified to original offset mapping."""
        tracker = ProvenanceTracker()
        segment = Segment(
            minified_start=0,
            minified_end=10,
            original_start=5,
            original_end=15,
        )
        source_map = SourceMap([segment])

        map_id = tracker.register(source_map, "test.py")
        original = tracker.minified_to_original(map_id, 3)

        assert original == 8  # 5 + 3

    def test_original_to_minified(self):
        """Test original to minified offset mapping."""
        tracker = ProvenanceTracker()
        segment = Segment(
            minified_start=0,
            minified_end=10,
            original_start=5,
            original_end=15,
        )
        source_map = SourceMap([segment])

        map_id = tracker.register(source_map, "test.py")
        minified = tracker.original_to_minified(map_id, 8)

        assert minified == 3  # 8 - 5

    def test_clear(self):
        """Test clearing all source maps."""
        tracker = ProvenanceTracker()
        segment = Segment(
            minified_start=0,
            minified_end=10,
            original_start=0,
            original_end=10,
        )
        source_map = SourceMap([segment])

        tracker.register(source_map, "test.py")
        assert len(tracker) == 1

        tracker.clear()
        assert len(tracker) == 0


class TestIngestorStats:
    """Tests for IngestorStats."""

    def test_init_zeros(self):
        """Test that stats initialize to zero."""
        stats = IngestorStats()
        assert stats.files_discovered == 0
        assert stats.files_processed == 0
        assert stats.files_skipped == 0
        assert stats.files_failed == 0
        assert stats.nodes_created == 0
        assert stats.edges_created == 0

    def test_repr(self):
        """Test string representation."""
        stats = IngestorStats()
        stats.files_processed = 5
        repr_str = repr(stats)

        assert "IngestorStats" in repr_str
        assert "processed=5" in repr_str


class TestDefaultExclusions:
    """Tests for default exclusion patterns."""

    def test_node_modules_excluded(self):
        """Test that node_modules is in exclusions."""
        assert "node_modules" in DEFAULT_EXCLUSIONS

    def test_git_excluded(self):
        """Test that .git is in exclusions."""
        assert ".git" in DEFAULT_EXCLUSIONS

    def test_pycache_excluded(self):
        """Test that __pycache__ is in exclusions."""
        assert "__pycache__" in DEFAULT_EXCLUSIONS

    def test_venv_excluded(self):
        """Test that .venv is in exclusions."""
        assert ".venv" in DEFAULT_EXCLUSIONS


class TestLanguageExtensions:
    """Tests for language extension mapping."""

    def test_python_extensions(self):
        """Test Python file extensions."""
        assert LANGUAGE_EXTENSIONS[".py"] == "python"
        assert LANGUAGE_EXTENSIONS[".pyw"] == "python"

    def test_typescript_extensions(self):
        """Test TypeScript file extensions."""
        assert LANGUAGE_EXTENSIONS[".ts"] == "typescript"
        assert LANGUAGE_EXTENSIONS[".tsx"] == "typescript"

    def test_javascript_extensions(self):
        """Test JavaScript file extensions."""
        assert LANGUAGE_EXTENSIONS[".js"] == "javascript"
        assert LANGUAGE_EXTENSIONS[".jsx"] == "javascript"
        assert LANGUAGE_EXTENSIONS[".mjs"] == "javascript"


class TestIngestorInit:
    """Tests for Ingestor initialization."""

    def test_init_valid_directory(self, tmp_path: Path):
        """Test initialization with valid directory."""
        ingestor = Ingestor(tmp_path)
        assert ingestor.project_root == tmp_path
        assert ingestor.graph.node_count == 0
        assert len(ingestor.tracker) == 0

    def test_init_nonexistent_raises(self):
        """Test initialization with non-existent path raises."""
        with pytest.raises(ValueError, match="does not exist"):
            Ingestor("/nonexistent/path")

    def test_init_file_raises(self, tmp_path: Path):
        """Test initialization with file instead of directory raises."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1")

        with pytest.raises(ValueError, match="not a directory"):
            Ingestor(test_file)

    def test_repr(self, tmp_path: Path):
        """Test string representation."""
        ingestor = Ingestor(tmp_path)
        repr_str = repr(ingestor)

        assert "Ingestor" in repr_str
        assert str(tmp_path) in repr_str


class TestIngestorExclusions:
    """Tests for file exclusion logic."""

    def test_exclude_node_modules(self, tmp_path: Path):
        """Test that node_modules is excluded."""
        # Create a node_modules directory with a file
        node_modules = tmp_path / "node_modules"
        node_modules.mkdir()
        (node_modules / "package.js").write_text("module.exports = {}")

        ingestor = Ingestor(tmp_path)
        files = list(ingestor._walk_files())

        assert len(files) == 0

    def test_exclude_pycache(self, tmp_path: Path):
        """Test that __pycache__ is excluded."""
        # Create a __pycache__ directory
        pycache = tmp_path / "__pycache__"
        pycache.mkdir()
        (pycache / "module.cpython-312.pyc").write_bytes(b"\x00\x00")

        ingestor = Ingestor(tmp_path)
        files = list(ingestor._walk_files())

        assert len(files) == 0

    def test_exclude_git(self, tmp_path: Path):
        """Test that .git is excluded."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "config").write_text("[core]")

        ingestor = Ingestor(tmp_path)
        files = list(ingestor._walk_files())

        assert len(files) == 0

    def test_gitignore_respected(self, tmp_path: Path):
        """Test that .gitignore patterns are respected."""
        # Create .gitignore
        (tmp_path / ".gitignore").write_text("ignored.py\n")

        # Create files
        (tmp_path / "included.py").write_text("x = 1")
        (tmp_path / "ignored.py").write_text("y = 2")

        ingestor = Ingestor(tmp_path)
        files = list(ingestor._walk_files())

        file_names = [f.name for f in files]
        assert "included.py" in file_names
        assert "ignored.py" not in file_names

    def test_unsupported_extension_skipped(self, tmp_path: Path):
        """Test that unsupported file extensions are skipped."""
        (tmp_path / "data.json").write_text('{"key": "value"}')
        (tmp_path / "readme.md").write_text("# Readme")
        (tmp_path / "script.py").write_text("x = 1")

        ingestor = Ingestor(tmp_path)
        files = list(ingestor._walk_files())

        file_names = [f.name for f in files]
        assert "script.py" in file_names
        assert "data.json" not in file_names
        assert "readme.md" not in file_names


class TestIngestorFileWalking:
    """Tests for file walking."""

    def test_walk_empty_directory(self, tmp_path: Path):
        """Test walking an empty directory."""
        ingestor = Ingestor(tmp_path)
        files = list(ingestor._walk_files())

        assert len(files) == 0

    def test_walk_python_files(self, tmp_path: Path):
        """Test walking Python files."""
        (tmp_path / "main.py").write_text("def main(): pass")
        (tmp_path / "utils.py").write_text("def util(): pass")

        ingestor = Ingestor(tmp_path)
        files = list(ingestor._walk_files())

        assert len(files) == 2
        file_names = {f.name for f in files}
        assert file_names == {"main.py", "utils.py"}

    def test_walk_typescript_files(self, tmp_path: Path):
        """Test walking TypeScript files."""
        (tmp_path / "app.ts").write_text("function app() {}")
        (tmp_path / "utils.tsx").write_text("const Component = () => null;")

        ingestor = Ingestor(tmp_path)
        files = list(ingestor._walk_files())

        assert len(files) == 2

    def test_walk_nested_directories(self, tmp_path: Path):
        """Test walking nested directory structure."""
        # Create nested structure
        sub_dir = tmp_path / "src" / "utils"
        sub_dir.mkdir(parents=True)

        (tmp_path / "main.py").write_text("x = 1")
        (sub_dir / "helper.py").write_text("y = 2")

        ingestor = Ingestor(tmp_path)
        files = list(ingestor._walk_files())

        assert len(files) == 2


class TestIngestorProcessing:
    """Tests for file processing."""

    def test_process_python_file(self, tmp_path: Path):
        """Test processing a Python file."""
        python_file = tmp_path / "example.py"
        python_file.write_text("""
def hello():
    print("Hello")

class MyClass:
    pass
""")

        ingestor = Ingestor(tmp_path)
        success = ingestor.ingest_file(python_file)

        assert success is True
        assert ingestor.stats.files_processed == 1
        assert ingestor.graph.node_count > 0

    def test_process_typescript_file(self, tmp_path: Path):
        """Test processing a TypeScript file."""
        ts_file = tmp_path / "example.ts"
        ts_file.write_text("""
function greet(name: string): string {
    return "Hello " + name;
}

class MyService {
}
""")

        ingestor = Ingestor(tmp_path)
        success = ingestor.ingest_file(ts_file)

        assert success is True
        assert ingestor.stats.files_processed == 1

    def test_process_file_creates_module_node(self, tmp_path: Path):
        """Test that processing creates a module node."""
        python_file = tmp_path / "module.py"
        python_file.write_text("x = 1")

        ingestor = Ingestor(tmp_path)
        ingestor.ingest_file(python_file)

        # Should have at least the module node
        module_nodes = ingestor.graph.find_by_type(NodeType.MODULE)
        assert len(module_nodes) >= 1

    def test_process_file_creates_function_nodes(self, tmp_path: Path):
        """Test that processing creates function nodes."""
        python_file = tmp_path / "funcs.py"
        python_file.write_text("""
def foo():
    pass

def bar():
    pass
""")

        ingestor = Ingestor(tmp_path)
        ingestor.ingest_file(python_file)

        func_nodes = ingestor.graph.find_by_type(NodeType.FUNCTION)
        assert len(func_nodes) == 2

    def test_process_file_creates_class_nodes(self, tmp_path: Path):
        """Test that processing creates class nodes."""
        python_file = tmp_path / "classes.py"
        python_file.write_text("""
class First:
    pass

class Second:
    pass
""")

        ingestor = Ingestor(tmp_path)
        ingestor.ingest_file(python_file)

        class_nodes = ingestor.graph.find_by_type(NodeType.CLASS)
        assert len(class_nodes) == 2

    def test_process_nonexistent_file(self, tmp_path: Path):
        """Test processing non-existent file."""
        ingestor = Ingestor(tmp_path)
        success = ingestor.ingest_file(tmp_path / "nonexistent.py")

        assert success is False
        assert (
            ingestor.stats.files_failed == 0
        )  # File doesn't exist, not counted as failed

    def test_process_file_with_encoding_error(self, tmp_path: Path):
        """Test processing file with encoding error doesn't crash."""
        binary_file = tmp_path / "binary.py"
        binary_file.write_bytes(b"\x80\x81\x82")

        ingestor = Ingestor(tmp_path)
        success = ingestor.ingest_file(binary_file)

        assert success is False
        assert ingestor.stats.files_failed == 1


class TestIngestorFullIngestion:
    """Tests for full ingestion pipeline."""

    def test_ingest_empty_project(self, tmp_path: Path):
        """Test ingesting an empty project."""
        ingestor = Ingestor(tmp_path)
        graph, tracker, stats = ingestor.ingest()

        assert graph.node_count == 0
        assert len(tracker) == 0
        assert stats.files_processed == 0

    def test_ingest_simple_project(self, tmp_path: Path):
        """Test ingesting a simple project structure."""
        # Create project structure
        (tmp_path / "main.py").write_text("""
def main():
    print("Hello")

if __name__ == "__main__":
    main()
""")
        (tmp_path / "utils.py").write_text("""
def helper():
    return 42
""")

        ingestor = Ingestor(tmp_path)
        graph, tracker, stats = ingestor.ingest()

        assert stats.files_processed == 2
        assert graph.node_count > 0
        assert len(tracker) > 0

    def test_ingest_mixed_languages(self, tmp_path: Path):
        """Test ingesting project with multiple languages."""
        (tmp_path / "app.py").write_text("def py_func(): pass")
        (tmp_path / "app.ts").write_text("function ts_func() {}")
        (tmp_path / "app.js").write_text("function js_func() {}")

        ingestor = Ingestor(tmp_path)
        graph, tracker, stats = ingestor.ingest()

        assert stats.files_processed == 3

    def test_ingest_creates_contains_edges(self, tmp_path: Path):
        """Test that ingestion creates CONTAINS edges from module to definitions."""
        (tmp_path / "example.py").write_text("""
def my_func():
    pass
""")

        ingestor = Ingestor(tmp_path)
        graph, _, _ = ingestor.ingest()

        # Should have CONTAINS edge from module to function
        assert graph.edge_count > 0

    def test_ingest_registers_source_maps(self, tmp_path: Path):
        """Test that ingestion registers source maps."""
        (tmp_path / "code.py").write_text("def example(): pass")

        ingestor = Ingestor(tmp_path)
        _, tracker, _ = ingestor.ingest()

        assert len(tracker) > 0

    def test_ingest_graceful_error_handling(self, tmp_path: Path):
        """Test that ingestion continues after file errors."""
        # Create mix of valid and invalid files
        (tmp_path / "valid.py").write_text("def valid(): pass")
        (tmp_path / "invalid.py").write_bytes(b"\x80\x81invalid bytes")
        (tmp_path / "also_valid.py").write_text("def also_valid(): pass")

        ingestor = Ingestor(tmp_path)
        graph, _, stats = ingestor.ingest()

        # Should process valid files despite one failure
        assert stats.files_processed >= 2
        assert stats.files_failed >= 1


class TestIngestorVisualization:
    """Tests for visualization through ingestor."""

    def test_to_mermaid_after_ingest(self, tmp_path: Path):
        """Test generating Mermaid diagram after ingestion."""
        (tmp_path / "app.py").write_text("""
def foo():
    pass

def bar():
    pass
""")

        ingestor = Ingestor(tmp_path)
        graph, _, _ = ingestor.ingest()

        mermaid = graph.to_mermaid()
        assert "graph LR" in mermaid
        assert "foo" in mermaid
        assert "bar" in mermaid


class TestIngestorTimestampTracking:
    """Tests for file timestamp tracking (lazy re-ingestion support)."""

    def test_timestamps_populated_after_ingest(self, tmp_path: Path):
        """Test that file timestamps are tracked after ingestion."""
        (tmp_path / "main.py").write_text("def main(): pass")
        (tmp_path / "utils.py").write_text("def util(): pass")

        ingestor = Ingestor(tmp_path)
        ingestor.ingest()

        # Timestamps should be tracked for both files
        assert len(ingestor._file_timestamps) == 2
        assert "main.py" in ingestor._file_timestamps
        assert "utils.py" in ingestor._file_timestamps

    def test_timestamps_are_valid(self, tmp_path: Path):
        """Test that stored timestamps are valid floating point numbers."""
        (tmp_path / "test.py").write_text("x = 1")

        ingestor = Ingestor(tmp_path)
        ingestor.ingest()

        timestamp = ingestor._file_timestamps.get("test.py")
        assert timestamp is not None
        assert isinstance(timestamp, float)
        assert timestamp > 0


class TestIngestorRefreshChangedFiles:
    """Tests for refresh_changed_files lazy re-ingestion."""

    def test_refresh_no_changes(self, tmp_path: Path):
        """Test refresh when no files have changed."""
        (tmp_path / "stable.py").write_text("def stable(): pass")

        ingestor = Ingestor(tmp_path)
        ingestor.ingest()

        # No changes - should return empty list
        refreshed = ingestor.refresh_changed_files()
        assert refreshed == []

    def test_refresh_modified_file(self, tmp_path: Path):
        """Test refresh detects and re-ingests modified file."""
        import os
        import time

        test_file = tmp_path / "changing.py"
        test_file.write_text("def original(): pass")

        ingestor = Ingestor(tmp_path)
        ingestor.ingest()

        # Modify the file - ensure timestamp changes
        time.sleep(0.1)  # Ensure different timestamp
        test_file.write_text("def modified(): pass\ndef extra(): pass")
        os.utime(test_file, None)  # Touch to update mtime

        # Refresh should detect the change
        refreshed = ingestor.refresh_changed_files()

        assert "changing.py" in refreshed
        assert len(refreshed) == 1

    def test_refresh_deleted_file(self, tmp_path: Path):
        """Test refresh handles deleted files."""
        test_file = tmp_path / "temporary.py"
        test_file.write_text("def temp(): pass")

        ingestor = Ingestor(tmp_path)
        ingestor.ingest()

        # Verify file is tracked
        assert "temporary.py" in ingestor._file_timestamps
        assert ingestor.graph.node_count > 0

        # Delete the file
        test_file.unlink()

        # Refresh should detect deletion
        refreshed = ingestor.refresh_changed_files()

        assert "temporary.py" in refreshed
        # File should no longer be tracked
        assert "temporary.py" not in ingestor._file_timestamps

    def test_refresh_removes_old_nodes(self, tmp_path: Path):
        """Test that refresh removes old nodes before re-ingesting."""
        import os
        import time

        test_file = tmp_path / "test.py"
        test_file.write_text("""
def func_a():
    pass

def func_b():
    pass
""")

        ingestor = Ingestor(tmp_path)
        ingestor.ingest()

        # Should have module + 2 functions
        initial_funcs = ingestor.graph.find_by_type(NodeType.FUNCTION)
        func_names = {f.name for f in initial_funcs}
        assert "func_a" in func_names
        assert "func_b" in func_names

        # Modify to have different functions
        time.sleep(0.1)
        test_file.write_text("""
def func_c():
    pass

def func_d():
    pass
""")
        os.utime(test_file, None)

        # Refresh
        ingestor.refresh_changed_files()

        # Old functions should be gone, new ones present
        updated_funcs = ingestor.graph.find_by_type(NodeType.FUNCTION)
        func_names = {f.name for f in updated_funcs}

        assert "func_a" not in func_names
        assert "func_b" not in func_names
        assert "func_c" in func_names
        assert "func_d" in func_names

    def test_refresh_updates_timestamp(self, tmp_path: Path):
        """Test that refresh updates the stored timestamp."""
        import os
        import time

        test_file = tmp_path / "updating.py"
        test_file.write_text("x = 1")

        ingestor = Ingestor(tmp_path)
        ingestor.ingest()

        original_timestamp = ingestor._file_timestamps["updating.py"]

        # Modify file
        time.sleep(0.1)
        test_file.write_text("x = 2")
        os.utime(test_file, None)

        ingestor.refresh_changed_files()

        new_timestamp = ingestor._file_timestamps["updating.py"]
        assert new_timestamp > original_timestamp

    def test_refresh_multiple_changed_files(self, tmp_path: Path):
        """Test refresh handles multiple changed files."""
        import os
        import time

        (tmp_path / "file1.py").write_text("def f1(): pass")
        (tmp_path / "file2.py").write_text("def f2(): pass")
        (tmp_path / "file3.py").write_text("def f3(): pass")

        ingestor = Ingestor(tmp_path)
        ingestor.ingest()

        # Modify two files
        time.sleep(0.1)
        (tmp_path / "file1.py").write_text("def f1_modified(): pass")
        (tmp_path / "file3.py").write_text("def f3_modified(): pass")
        os.utime(tmp_path / "file1.py", None)
        os.utime(tmp_path / "file3.py", None)

        refreshed = ingestor.refresh_changed_files()

        assert len(refreshed) == 2
        assert "file1.py" in refreshed
        assert "file3.py" in refreshed
        assert "file2.py" not in refreshed

    def test_refresh_is_synchronous(self, tmp_path: Path):
        """Test that refresh operation is synchronous (returns immediately)."""
        import time

        (tmp_path / "test.py").write_text("def sync(): pass")

        ingestor = Ingestor(tmp_path)
        ingestor.ingest()

        start = time.time()
        refreshed = ingestor.refresh_changed_files()
        elapsed = time.time() - start

        # Should be fast (no background thread, no polling)
        assert elapsed < 1.0
        assert isinstance(refreshed, list)
