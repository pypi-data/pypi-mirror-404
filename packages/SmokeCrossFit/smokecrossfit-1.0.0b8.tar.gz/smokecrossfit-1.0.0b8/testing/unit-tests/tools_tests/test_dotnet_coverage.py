from pathlib import Path
import pytest
import crossfit
from crossfit import DotnetCoverage, Command
from crossfit.executors import LocalExecutor
from crossfit.models import CommandResult, ReportFormat


@pytest.fixture
def dotnetcoverage_tool(logger):
    return DotnetCoverage(logger, crossfit.refs.tools_dir, True)


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


def _mock_execute_success(monkeypatch, local_executor, command: Command) -> CommandResult:
    mock_result = CommandResult(code=0, command=str(command), output="", error="")
    monkeypatch.setattr(local_executor, "execute", lambda cmd: mock_result)
    return mock_result


@pytest.mark.usefixtures("monkeypatch")
def test_dotnetcoverage_execute_report(
        monkeypatch,
        dotnetcoverage_tool,
        local_executor,
        coverage_files,
        target_dir,
        sourcecode_dir
):
    report_format = ReportFormat.Csv
    report_formats = [ReportFormat.Html, ReportFormat.Xml]

    command = dotnetcoverage_tool.save_report(
        coverage_files, target_dir, sourcecode_dir, report_format, report_formats)
    assert isinstance(command, Command)

    _mock_execute_success(monkeypatch, local_executor, command)

    result = local_executor.execute(command)
    assert isinstance(result, CommandResult)
    assert result.code == 0


@pytest.mark.usefixtures("monkeypatch")
def test_dotnetcoverage_merge_coverage(monkeypatch, dotnetcoverage_tool, local_executor, coverage_files, target_dir):
    target_file = Path("merged.exec")

    command = dotnetcoverage_tool.merge_coverage(coverage_files, target_dir, target_file)
    assert isinstance(command, Command)

    _mock_execute_success(monkeypatch, local_executor, command)

    result = local_executor.execute(command)
    assert isinstance(result, CommandResult)
    assert result.code == 0


@pytest.mark.usefixtures("monkeypatch")
def test_dotnetcoverage_snapshot_coverage_with_mocked_execute(monkeypatch, dotnetcoverage_tool, local_executor):
    session = "dummy_session"
    target_dir = Path("dummy_dir")
    target_file = Path("snapshot.exec")

    command = dotnetcoverage_tool.snapshot_coverage(session, target_dir, target_file)
    assert isinstance(command, Command)

    _mock_execute_success(monkeypatch, local_executor, command)

    result = local_executor.execute(command)
    assert isinstance(result, CommandResult)
    assert result.code == 0


@pytest.mark.usefixtures("monkeypatch")
def test_dotnetcoverage_reset_coverage_with_mocked_execute(monkeypatch, dotnetcoverage_tool, local_executor):
    session = "dummy_session"

    command = dotnetcoverage_tool.reset_coverage(session)
    assert isinstance(command, Command)

    _mock_execute_success(monkeypatch, local_executor, command)

    result = local_executor.execute(command)
    assert isinstance(result, CommandResult)
    assert result.code == 0


