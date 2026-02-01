import os.path
from pathlib import Path
from typing import Optional, Tuple
from crossfit import Command
from crossfit.commands.command_builder import CommandBuilder
from crossfit.models.tool_models import ReportFormat, ToolType
from crossfit.tools.tool import Tool


class Jacoco(Tool):
    """JaCoCo coverage tool implementation for Java projects."""
    _tool_type = ToolType.Jacoco

    def _create_command_builder(self, command, tool_type = None, path_arguments = None, required_flags = None,
                                *extras: Tuple[str, Optional[str]]) -> CommandBuilder:
        """
        Creates a CommandBuilder for JaCoCo CLI commands.
        :param command: The JaCoCo command to execute (e.g., 'report', 'dump', 'merge').
        :param tool_type: The tool type used to build the command on (defaults to self._tool_type).
        :param path_arguments: Path arguments to add to the command (e.g., coverage files).
        :param required_flags: List of required flag options that must be present in extras.
        :param extras: Extra options to pass to the JaCoCo CLI as tuples of (option, value).
        :return: A CommandBuilder configured for the JaCoCo command.
        :raises ValueError: If required flags are missing and catch is False.
        """
        tool_type = tool_type or self._tool_type
        command_builder = (super()._create_command_builder(command, tool_type, path_arguments, *extras)
                           .set_execution_call(f"java -jar {os.path.relpath(Path(self._path) / str(tool_type.value))}"))

        required_flags = required_flags or []
        for required_flag in required_flags:
            if required_flag not in [extra[0] for extra in list(extras)]:
                msg = (f"Encountered error while building {tool_type.name} command. "
                       f"JaCoCo flag option {required_flag} is required for command '{command}'.")
                self._logger.error(msg)
                if not self._catch:
                    raise ValueError(msg)
                command_builder.set_command_body(["--help"])

        return command_builder

    def save_report(self, coverage_files, target_dir, report_format, report_formats, sourcecode_dir, build_dir, *extras)\
            -> Command:
        """
        Creates a JaCoCo coverage report from coverage files to the given path.
        :param coverage_files: File paths to JaCoCo .exec coverage files to create the report from.
        :param target_dir: Targeted directory to save the JaCoCo report to.
        :param report_format: Primary format of the JaCoCo report (e.g., HTML, XML, CSV).
        :param report_formats: Additional formats of JaCoCo reports to create.
        :param sourcecode_dir: Directory containing the covered source code files.
        :param build_dir: Directory containing the compiled class files (required for JaCoCo).
        :param extras: Extra options to pass to the JaCoCo CLI's report command.
        :return: A Command object configured to generate the coverage report.
        """
        if sourcecode_dir:
            extras += ("--sourcefiles", str(sourcecode_dir)),
        if build_dir:
            extras += ("--classfiles", str(build_dir)),
        command = self._create_command_builder(
            "report", None, coverage_files, ["--classfiles"], *extras)
        combined_formats = set((report_formats or []) + [report_format])
        for rf in combined_formats:
            if rf == ReportFormat.Html:
                command = command.add_option(f"--{rf.name.lower()}", str(target_dir))
            elif rf is not None:
                command = command.add_option(f"--{rf.name.lower()}",
                                             str((Path(target_dir) / self._get_default_target_filename())
                                                 .with_suffix(f".{rf.value.lower()}")))
        return command.build_command()

    def snapshot_coverage(self, session, target_dir, target_file, *extras) -> Command:
        """
        Triggers JaCoCo agent to dump coverage data to the given path.
        :param session: Session identifier (not used by JaCoCo dump but kept for interface consistency).
        :param target_dir: Targeted directory to save the JaCoCo coverage dump to.
        :param target_file: Specified snapshot file name - when not given, uses default with .exec suffix.
        :param extras: Extra options to pass to the JaCoCo CLI's dump command.
        :return: A Command object configured to dump coverage data.
        """
        target_path = Path(target_dir) / (
            target_file if target_file is not None else self._get_default_target_filename())
        if not target_path.suffix:
            target_path = target_path.with_suffix(".exec")
        extras += ("--destfile", str(target_path)),
        command = self._create_command_builder(
            "dump", None, None, None, *extras)
        return command.build_command()

    def merge_coverage(self, coverage_files, target_dir, target_file, *extras) -> Command:
        """
        Merges multiple JaCoCo coverage files into a single unified coverage file.
        :param coverage_files: File paths to JaCoCo .exec coverage files to merge.
        :param target_dir: Targeted directory to save the merged coverage file to.
        :param target_file: Specified merged file name - when not given, uses default with .exec suffix.
        :param extras: Extra options to pass to the JaCoCo CLI's merge command.
        :return: A Command object configured to merge coverage files.
        """
        target_path = Path(target_dir) / (
            target_file if target_file is not None else self._get_default_target_filename())
        if not target_path.suffix:
            target_path = target_path.with_suffix(".exec")
        extras += ("--destfile", str(target_path)),
        command = self._create_command_builder(
            "merge", None, coverage_files, None,*extras)
        return command.build_command()
