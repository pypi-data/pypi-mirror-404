import os.path
from pathlib import Path

import pytest

import crossfit
from crossfit import Jacoco, Command
from crossfit.executors import LocalExecutor
from crossfit.models import CommandResult, ReportFormat


@pytest.fixture
def jacoco_tool(logger):
    return Jacoco(logger, crossfit.refs.tools_dir, True)

@pytest.fixture
def local_executor(logger):
    return LocalExecutor(logger, False, **{"check": True})

@pytest.fixture
def coverage_files(tests_dir_path):
    return [Path(str(os.path.relpath(tests_dir_path / r"helpers/tools/jacoco/f1.exec"))),
            Path(str(os.path.relpath(tests_dir_path / r"helpers/tools/jacoco/f2.exec")))]


@pytest.fixture
def target_dir(tests_dir_path):
    return Path(str(os.path.relpath(tests_dir_path / r"helpers/tools/jacoco/output/")))


@pytest.fixture
def sourcecode_dir(tests_dir_path):
    return Path(str(os.path.relpath(tests_dir_path / r"helpers/tools/jacoco/sourcecode/")))


@pytest.fixture
def classfiles_dir(tests_dir_path):
    return Path(str(os.path.relpath(tests_dir_path / r"helpers/tools/jacoco/classfiles/")))


@pytest.mark.parametrize("report_format, report_formats, expected_return_code", [
    (ReportFormat.Csv, [ReportFormat.Html, ReportFormat.Xml], 0),
    (ReportFormat.Html, None, 0),
    (ReportFormat.Xml, [], 0),
], ids=[
    "Csv_Report_With_Html_And_Xml",
    "Html_Report",
    "Xml_Report_Only",
])
def test_jacoco_execute_report(jacoco_tool, local_executor, coverage_files, target_dir, sourcecode_dir, classfiles_dir,
                               report_format, report_formats, expected_return_code):
    extras = [("--quiet", None), ("--tabwith", "6")]

    command = jacoco_tool.save_report(
        coverage_files,
        target_dir,
        report_format,
        report_formats,
        sourcecode_dir,
        classfiles_dir,
        *extras
    )

    assert isinstance(command, Command)

    result = local_executor.execute(command)
    assert isinstance(result, CommandResult)
    assert result.code == expected_return_code


def test_jacoco_execute_report_files_wildcard(jacoco_tool, local_executor, target_dir, sourcecode_dir, classfiles_dir, tests_dir_path):
    report_format = ReportFormat.Csv
    coverage_files = [Path(tests_dir_path / r"helpers/tools/jacoco/*.exec")]
    report_formats = [ReportFormat.Html, ReportFormat.Xml]
    extras = [("--quiet", None), ("--tabwith", "6")]

    command = jacoco_tool.save_report(
        coverage_files,
        target_dir,
        report_format,
        report_formats,
        sourcecode_dir,
        classfiles_dir,
        *extras
    )

    assert isinstance(command, Command)

    result = local_executor.execute(command)
    assert isinstance(result, CommandResult)
    assert result.code == 0


def test_jacoco_merge_coverage(jacoco_tool, local_executor, coverage_files, target_dir):
    target_file = Path("merged.exec")
    extras = []

    command = jacoco_tool.merge_coverage(coverage_files, target_dir, target_file, *extras)
    assert isinstance(command, Command)

    result = local_executor.execute(command)
    assert isinstance(result, CommandResult)
    assert result.code == 0
