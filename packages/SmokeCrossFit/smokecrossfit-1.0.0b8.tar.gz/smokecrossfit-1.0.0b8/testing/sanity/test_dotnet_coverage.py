import pytest
from pathlib import Path
from crossfit import DotnetCoverage, Command
from crossfit.executors import LocalExecutor
from crossfit.models import CommandResult, ReportFormat


@pytest.fixture
def dotnetcoverage_tool(logger):
    return DotnetCoverage(logger, catch=True)


@pytest.fixture
def local_executor(logger):
    return LocalExecutor(logger, False, **{"check": True})


@pytest.fixture
def coverage_files(tests_dir_path):
    return [Path(tests_dir_path / r"helpers/tools/dotnetcoverage/s1.cobertura.xml"),
            Path(tests_dir_path / r"helpers/tools/dotnetcoverage/s2.cobertura.xml")]


@pytest.fixture
def target_dir(tests_dir_path):
    return Path(tests_dir_path / r"helpers/tools/dotnetcoverage/output/")


@pytest.fixture
def sourcecode_dir(tests_dir_path):
    return Path(tests_dir_path / r"helpers/tools/dotnetcoverage/sourcecode/")


@pytest.mark.parametrize("report_format, report_formats, expected_return_code", [
    (None, [ReportFormat.Html, ReportFormat.Xml], 0),
    (ReportFormat.Html, None, 0),
    (ReportFormat.Xml, [], 0),
], ids=[
    "Csv_Report_With_Html_And_Xml",
    "Html_Report",
    "Xml_Report_Only",
])
def test_dotnetcoverage_execute_report(dotnetcoverage_tool, local_executor, coverage_files, target_dir, sourcecode_dir,
                                       report_format, report_formats, expected_return_code):
    command = dotnetcoverage_tool.save_report(
        coverage_files, target_dir, sourcecode_dir, report_format, report_formats)

    assert isinstance(command, Command)

    result = local_executor.execute(command)
    assert isinstance(result, CommandResult)
    assert result.code == expected_return_code


def test_dotnetcoverage_merge_coverage(dotnetcoverage_tool, local_executor, coverage_files, target_dir):
    target_file = Path("merged")

    command = dotnetcoverage_tool.merge_coverage(coverage_files, target_dir, target_file)
    assert isinstance(command, Command)

    result = local_executor.execute(command)
    assert isinstance(result, CommandResult)
    assert result.code == 0
