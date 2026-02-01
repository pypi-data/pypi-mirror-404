import tempfile
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Collection, Optional, Tuple, List, Union
from crossfit.commands.command import Command
from crossfit.commands.command_builder import CommandBuilder
from crossfit.models.tool_models import ToolType


class Tool(ABC):
    """Abstract base class for coverage tools. Tools build and return Commands."""
    _tool_type: ToolType
    _path: Optional[Path]
    _logger: logging.Logger
    _catch: bool

    def __init__(self, logger: logging.Logger, path: Optional[Path] = None, catch: bool = True):
        """
        :param logger: Logger instance for logging (required).
        :param path: The path to the tool executable/jar.
        :param catch: If True, catches exceptions and returns fallback. If False, re-raises.
        """
        self._logger: logging.Logger = logger
        self._path: Optional[Path] = path
        self._catch: bool = catch

    def _get_default_target_filename(self) -> str:
        """Returns the default target filename for this tool."""
        return f"cross-{self._tool_type.name}".lower()

    def _create_command_builder(self, command: str, tool_type: Optional[ToolType] = None,
                             path_arguments: Optional[Collection[Path]] = None,
                             *extras: Tuple[str, Optional[str]]) -> CommandBuilder:
        """
        Creates a CommandBuilder for the tool's wanted functionality.
        :param command: The command of the tool to build on.
        :param tool_type: The tool type used to build the command on (defaults to self._tool_type).
        :param path_arguments: Path arguments to add to the command.
        :param extras: Extra options to pass to the CLI's command as tuples of (option, value).
        :returns: A CommandBuilder configured for this tool command.
        """
        tool_type = tool_type or self._tool_type
        path_arguments = path_arguments or []

        command_builder = CommandBuilder().set_execution_call(str(tool_type.value), self._path)
        try:
            return command_builder.set_command_to_execute(command).add_path_arguments(*path_arguments).add_options(
                *extras)
        except FileNotFoundError as e:
            self._logger.error(f"Encountered exception while building {tool_type.name} command. Error - {e}")
            if not self._catch:
                raise
            return command_builder.set_command_body(["--help"])

    @abstractmethod
    def save_report(self, coverage_files: List[Union[Path, str]], target_dir: Path, report_format, report_formats,
                    sourcecode_dir: Optional[Path], build_dir: Optional[Path],
                    *extras: Tuple[str, Optional[str]]) -> Command:
        """Builds a command to create a coverage report."""
        raise NotImplementedError

    @abstractmethod
    def snapshot_coverage(self, session: str, target_dir: Path, target_file: Optional[Path],
                          *extras: Tuple[str, Optional[str]]) -> Command:
        """Builds a command to snapshot coverage data."""
        raise NotImplementedError

    @abstractmethod
    def merge_coverage(self, coverage_files: List[Union[Path, str]], target_dir: Path, target_file: Optional[Path],
                       *extras: Tuple[str, Optional[str]]) -> Command:
        """Builds a command to merge coverage files."""
        raise NotImplementedError

    def reset_coverage(self, session: str, *extras: Tuple[str, Optional[str]]) -> Command:
        """
        Builds a command to reset coverage data.
        Uses next_command chaining to snapshot with --reset flag and then clean up temp file.
        :param session: Session id of the coverage agent.
        :param extras: Extra options to pass to the CLI's command.
        :returns: A Command with chained cleanup command via next_command.
        """
        target_dir = Path(tempfile.gettempdir()) / r"crossfit"
        extras = extras + (("--reset", None),)

        snapshot_command = self.snapshot_coverage(session, target_dir, None, *extras)
        cleanup_command = CommandBuilder().with_command(["rm", "-f", str(target_dir)]).build_command()
        snapshot_command.next_command = cleanup_command

        return snapshot_command
