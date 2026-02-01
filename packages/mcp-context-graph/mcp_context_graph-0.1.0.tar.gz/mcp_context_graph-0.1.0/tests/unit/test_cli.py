"""Tests for CLI module."""

import contextlib
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

from mcp_context_graph.cli import create_parser, main


class TestCLI:
    """Tests for CLI functions."""

    def test_create_parser(self) -> None:
        """Test that argument parser is created correctly."""
        parser = create_parser()
        assert parser.prog == "mcp-context-graph"

    def test_parser_version(self) -> None:
        """Test --version argument."""
        parser = create_parser()
        # Version action raises SystemExit
        with (
            patch.object(sys, "argv", ["mcp-context-graph", "--version"]),
            contextlib.suppress(SystemExit),
        ):
            parser.parse_args(["--version"])

    def test_parser_default_path(self) -> None:
        """Test default project path is current directory."""
        parser = create_parser()
        args = parser.parse_args([])
        # Default is Path.cwd(), just check it's a Path
        assert hasattr(args, "project_path")

    def test_parser_custom_path(self) -> None:
        """Test custom project path argument."""
        parser = create_parser()
        args = parser.parse_args(["/some/path"])
        assert str(args.project_path) == "/some/path"

    def test_parser_stdio_flag(self) -> None:
        """Test --stdio flag."""
        parser = create_parser()
        args = parser.parse_args(["--stdio"])
        assert args.stdio is True

    def test_main_returns_zero_with_mocked_server(self) -> None:
        """Test main function returns 0 when server runs successfully."""
        with (
            patch.object(sys, "argv", ["mcp-context-graph"]),
            patch(
                "mcp_context_graph.mcp.server.run_server",
                new_callable=AsyncMock,
            ) as mock_run,
        ):
            mock_run.return_value = None
            result = main()
            assert result == 0
            # Verify run_server was called with current directory
            mock_run.assert_called_once()
            called_path = mock_run.call_args[0][0]
            assert isinstance(called_path, Path)

    def test_main_returns_one_for_nonexistent_path(self) -> None:
        """Test main function returns 1 for nonexistent path."""
        with patch.object(sys, "argv", ["mcp-context-graph", "/nonexistent/path"]):
            result = main()
            assert result == 1

    def test_main_returns_zero_on_keyboard_interrupt(self) -> None:
        """Test main function returns 0 on KeyboardInterrupt."""
        with (
            patch.object(sys, "argv", ["mcp-context-graph"]),
            patch(
                "mcp_context_graph.mcp.server.run_server",
                new_callable=AsyncMock,
                side_effect=KeyboardInterrupt,
            ),
        ):
            result = main()
            assert result == 0
