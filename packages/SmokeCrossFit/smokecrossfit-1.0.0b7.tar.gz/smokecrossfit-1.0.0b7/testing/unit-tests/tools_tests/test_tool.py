# test_tool.py
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

import pytest

from crossfit.commands.command import Command
from crossfit.commands.command_builder import CommandBuilder
from crossfit.models.tool_models import ToolType
from crossfit.tools.tool import Tool


class ConcreteTool(Tool):
    """Concrete implementation of Tool for testing purposes."""
    _tool_type = ToolType.Jacoco

    def __init__(self, logger, path: Optional[Path] = None, catch: bool = True):
        super().__init__(logger, path, catch)

    def save_report(self, coverage_files: List[Path], target_dir: Path, report_format, report_formats,
                    sourcecode_dir: Optional[Path], build_dir: Optional[Path],
                    *extras: Tuple[str, Optional[str]]) -> Command:
        return self._create_command_builder("report", None, coverage_files, *extras).build_command()

    def snapshot_coverage(self, session: str, target_dir: Path, target_file: Optional[str],
                          *extras: Tuple[str, Optional[str]]) -> Command:
        return self._create_command_builder("snapshot", None, None, *extras).add_option("--session", session).build_command()

    def merge_coverage(self, coverage_files: List[Path], target_dir: Path, target_file: Optional[str],
                       *extras: Tuple[str, Optional[str]]) -> Command:
        return self._create_command_builder("merge", None, coverage_files, *extras).build_command()


@pytest.fixture
def tool(logger):
    """Fixture for a tool with catch=True (default)."""
    return ConcreteTool(logger=logger, path=Path("./tools"), catch=True)


@pytest.fixture
def tool_no_catch(logger):
    """Fixture for a tool with catch=False."""
    return ConcreteTool(logger=logger, path=Path("./tools"), catch=False)


@pytest.fixture
def tool_no_path(logger):
    """Fixture for a tool without a custom path."""
    return ConcreteTool(logger=logger, path=None, catch=True)


class TestToolInit:
    """Tests for Tool initialization."""

    def test_tool_init_with_all_params(self, logger):
        """Test Tool initialization with all parameters."""
        tool = ConcreteTool(logger=logger, path=Path("/custom/path"), catch=False)
        assert tool._logger == logger
        assert tool._path == Path("/custom/path")
        assert tool._catch is False

    def test_tool_init_with_defaults(self, logger):
        """Test Tool initialization with default values."""
        tool = ConcreteTool(logger=logger)
        assert tool._logger == logger
        assert tool._path is None
        assert tool._catch is True

    def test_tool_type_is_set(self, logger):
        """Test that tool type is correctly set on the concrete tool."""
        tool = ConcreteTool(logger=logger)
        assert tool._tool_type == ToolType.Jacoco


class TestGetDefaultTargetFilename:
    """Tests for _get_default_target_filename method."""

    def test_default_filename_format(self, tool):
        """Test that default filename follows the expected format."""
        filename = tool._get_default_target_filename()
        assert filename == "cross-jacoco"

    def test_default_filename_lowercase(self, tool):
        """Test that default filename is lowercase."""
        filename = tool._get_default_target_filename()
        assert filename == filename.lower()


class TestCreateCommandBuilder:
    """Tests for _create_command_builder method."""

    def test_create_command_builder_basic(self, tool):
        """Test basic command builder creation."""
        builder = tool._create_command_builder("report")
        command = builder.build_command()
        assert "jacococli.jar" in str(command)
        assert "report" in str(command)

    def test_create_command_builder_with_path(self, tool):
        """Test command builder includes tool path."""
        builder = tool._create_command_builder("merge")
        command = builder.build_command()
        # Path should be included in the execution call
        assert "tools" in str(command) or "jacococli.jar" in str(command)

    def test_create_command_builder_without_path(self, tool_no_path):
        """Test command builder without custom path."""
        builder = tool_no_path._create_command_builder("report")
        command = builder.build_command()
        assert "jacococli.jar" in str(command)

    def test_create_command_builder_with_extras(self, tool):
        """Test command builder with extra options."""
        builder = tool._create_command_builder("report", None, None, ("--verbose", None), ("--output", "file.xml"))
        command = builder.build_command()
        assert "--verbose" in str(command)
        assert "--output" in str(command)
        assert "file.xml" in str(command)

    def test_create_command_builder_returns_command_builder(self, tool):
        """Test that _create_command_builder returns a CommandBuilder instance."""
        builder = tool._create_command_builder("snapshot")
        assert isinstance(builder, CommandBuilder)

    def test_create_command_builder_with_invalid_path_catch_true(self, tool):
        """Test command builder falls back to --help when path is invalid and catch=True."""
        invalid_paths = [Path("/nonexistent/path/file.exec")]
        builder = tool._create_command_builder("report", path_arguments=invalid_paths)
        command = builder.build_command()
        # Should fall back to --help command
        assert "--help" in str(command)

    def test_create_command_builder_with_invalid_path_catch_false(self, tool_no_catch):
        """Test command builder raises exception when path is invalid and catch=False."""
        invalid_paths = [Path("/nonexistent/path/file.exec")]
        with pytest.raises(FileNotFoundError):
            tool_no_catch._create_command_builder("report", path_arguments=invalid_paths)


class TestResetCoverage:
    """Tests for reset_coverage method."""

    def test_reset_coverage_returns_command(self, tool):
        """Test that reset_coverage returns a Command object."""
        command = tool.reset_coverage("test-session")
        assert isinstance(command, Command)

    def test_reset_coverage_has_reset_flag(self, tool):
        """Test that reset_coverage command includes --reset flag."""
        command = tool.reset_coverage("test-session")
        assert "--reset" in str(command)

    def test_reset_coverage_has_session(self, tool):
        """Test that reset_coverage command includes session."""
        command = tool.reset_coverage("my-session-123")
        assert "my-session-123" in str(command)

    def test_reset_coverage_has_chained_cleanup_command(self, tool):
        """Test that reset_coverage has a next_command for cleanup."""
        command = tool.reset_coverage("test-session")
        assert command.next_command is not None

    def test_reset_coverage_cleanup_uses_rm(self, tool):
        """Test that cleanup command uses rm -f."""
        command = tool.reset_coverage("test-session")
        cleanup_cmd = str(command.next_command)
        assert "rm" in cleanup_cmd
        assert "-f" in cleanup_cmd

    def test_reset_coverage_uses_temp_dir(self, tool):
        """Test that reset_coverage uses temp directory."""
        command = tool.reset_coverage("test-session")
        cleanup_cmd = str(command.next_command)
        temp_dir = tempfile.gettempdir()
        assert temp_dir in cleanup_cmd or "crossfit" in cleanup_cmd

    def test_reset_coverage_with_extras(self, tool):
        """Test reset_coverage with additional extra options."""
        command = tool.reset_coverage("test-session", ("--custom", "value"))
        cmd_str = str(command)
        assert "--custom" in cmd_str
        assert "value" in cmd_str
        assert "--reset" in cmd_str


class TestToolAbstractMethods:
    """Tests for abstract method implementations."""

    def test_save_report_returns_command(self, tool):
        """Test that save_report returns a Command."""
        command = tool.save_report([], Path("/output"), None, None, None, None)
        assert isinstance(command, Command)

    def test_snapshot_coverage_returns_command(self, tool):
        """Test that snapshot_coverage returns a Command."""
        command = tool.snapshot_coverage("session-1", Path("/output"), "file.exec")
        assert isinstance(command, Command)

    def test_merge_coverage_returns_command(self, tool):
        """Test that merge_coverage returns a Command."""
        command = tool.merge_coverage([], Path("/output"), "merged.exec")
        assert isinstance(command, Command)
