from pathlib import Path
from typing import List, Tuple, Optional

from crossfit import Command
from crossfit.models import ReportFormat, ToolType
from crossfit.tools.tool import Tool


class DotnetCoverage(Tool):
    _tool_type = ToolType.DotnetCoverage

    def snapshot_coverage(self, session, target_dir, target_file, *extras: Tuple[str, Optional[str]]) -> Command:
        """
        Triggers dotnet-coverage agent to save cobertura formatted coverage files to the given path.
        :param session: Session id of the dotnet-coverage agent collected-coverage to snapshot.
        :param target_dir: Targeted directory to save the dotnet-coverage collection to.
        :param target_file: Specified snapshot file name - when not given, uses default with .xml suffix.
        :param extras: Extra options to pass to the dotnet-coverage CLI's snapshot command.
        :return: A Command object configured to snapshot coverage data.
        """
        target_path = Path(target_dir) / (
            target_file if target_file is not None else self._get_default_target_filename())
        if not target_path.suffix:
            target_path = target_path.with_suffix(".xml")
        extras += ("--output", str(target_path)),
        command_builder = self._create_command_builder(
            "snapshot", None, None, *extras).add_arguments(session)

        return command_builder.build_command()

    def merge_coverage(self, coverage_files, target_dir, target_file, *extras: Tuple[str, Optional[str]]) -> Command:
        """
        Merges multiple coverage files into a single unified coverage file.
        :param coverage_files: File paths to coverage files to merge.
        :param target_dir: Targeted directory to save the merged coverage file to.
        :param target_file: Specified merged file name - when not given, uses default with .xml suffix.
        :param extras: Extra options to pass to the dotnet-coverage CLI's merge command.
        :return: A Command object configured to merge coverage files.
        """
        extras += ("--output", str(Path(target_dir) / (
            target_file if target_file is not None else Path(self._get_default_target_filename()).with_suffix(
                ".xml")))),
        command_builder = self._create_command_builder("merge", None, coverage_files, *extras)
        if {"--output-format", "-f"}.intersection(command_builder.build_command().command):
            command_builder = command_builder.add_option("--output-format", ReportFormat.Cobertura.value.lower())

        return command_builder.build_command()

    def save_report(self, coverage_files, target_dir, sourcecode_dir,
                    report_format: ReportFormat = None, report_formats: List[ReportFormat] = None,
                    *extras: Tuple[str, Optional[str]]) -> Command:
        """
        Creates a dotnet-coverage report from coverage files to the given path.
        :param coverage_files: File paths (can handle wildcards) to create dotnet-coverage report from.
        :param target_dir: Targeted directory to save the dotnet-coverage report to.
        :param sourcecode_dir: Directory containing the covered source code files.
        :param report_format: Primary format of the dotnet-coverage report.
        :param report_formats: Additional formats of dotnet-coverage reports to create.
        :param extras: Extra options to pass to the dotnet CLI's report command.
        :return: A Command object configured to generate the coverage report.
        """
        multiple_values_delimiter = ';'
        if sourcecode_dir:
            extras += ("-sourcedirs", str(sourcecode_dir)),
        extras += ("-targetdir", str(target_dir)),
        command_builder = (
            self._create_command_builder("", ToolType.DotnetReportGenerator, None, *extras)
            .set_values_delimiter(":", True)
            .add_option("-reports", f"\"{multiple_values_delimiter.join(map(str, coverage_files))}\""))
        combined_formats = set((report_formats or []) + [report_format])
        command_builder = command_builder.add_option(
            "-reporttypes",f"\"{multiple_values_delimiter.join([rf.value for rf in combined_formats if rf])}\"")

        command = command_builder.build_command()
        command.command = [kw.replace("--", "-") for kw in command.command[2:]]

        return command
