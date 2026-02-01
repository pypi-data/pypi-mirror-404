from pathlib import Path

import pytest
import crossfit
from crossfit import Jacoco, Command
from crossfit.executors.local_executor import LocalExecutor
from crossfit.models import CommandResult, ReportFormat


@pytest.fixture
def jacoco_tool(logger):
    return Jacoco(logger, crossfit.refs.tools_dir, True)


@pytest.fixture
def local_executor(logger):
    return LocalExecutor(logger, False, **{"check": True})


@pytest.fixture
def coverage_files(tests_dir_path):
    return [
        Path(tests_dir_path / r"helpers/tools/jacoco/f1.exec"),
        Path(tests_dir_path / r"helpers/tools/jacoco/f2.exec"),
    ]


@pytest.fixture
def target_dir(tests_dir_path):
    return Path(tests_dir_path / r"helpers/tools/jacoco/output/")


@pytest.fixture
def sourcecode_dir(tests_dir_path):
    return Path(tests_dir_path / r"helpers/tools/jacoco/sourcecode/")


@pytest.fixture
def classfiles_dir(tests_dir_path):
    return Path(tests_dir_path / r"helpers/tools/jacoco/classfiles/")


def _mock_execute_success(monkeypatch, local_executor, command: Command) -> CommandResult:
    mock_result = CommandResult(code=0, command=str(command), output="", error="")
    monkeypatch.setattr(local_executor, "execute", lambda cmd: mock_result)
    return mock_result


def test_jacoco_execute_report(
    monkeypatch,
    jacoco_tool,
    local_executor,
    coverage_files,
    target_dir,
    sourcecode_dir,
    classfiles_dir,
):
    report_format = ReportFormat.Csv
    report_formats = [ReportFormat.Html, ReportFormat.Xml]

    command = jacoco_tool.save_report(
        coverage_files,
        target_dir,
        report_format,
        report_formats,
        sourcecode_dir,
        classfiles_dir,
    )
    assert isinstance(command, Command)

    _mock_execute_success(monkeypatch, local_executor, command)

    result = local_executor.execute(command)
    assert isinstance(result, CommandResult)
    assert result.code == 0


def test_jacoco_merge_coverage(
    monkeypatch,
    jacoco_tool,
    local_executor,
    coverage_files,
    target_dir,
):
    target_file = Path("merged.exec")

    command = jacoco_tool.merge_coverage(coverage_files, target_dir, target_file)
    assert isinstance(command, Command)

    _mock_execute_success(monkeypatch, local_executor, command)

    result = local_executor.execute(command)
    assert isinstance(result, CommandResult)
    assert result.code == 0


def test_jacoco_snapshot_coverage_with_mocked_execute(
    monkeypatch,
    jacoco_tool,
    local_executor,
):
    session = "dummy_session"
    target_dir = Path("dummy_dir")
    target_file = Path("snapshot.exec")

    command = jacoco_tool.snapshot_coverage(session, target_dir, target_file)
    assert isinstance(command, Command)

    _mock_execute_success(monkeypatch, local_executor, command)

    result = local_executor.execute(command)
    assert isinstance(result, CommandResult)
    assert result.code == 0


def test_jacoco_reset_coverage_with_mocked_execute(
    monkeypatch,
    jacoco_tool,
    local_executor,
):
    session = "dummy_session"

    command = jacoco_tool.reset_coverage(session)
    assert isinstance(command, Command)

    _mock_execute_success(monkeypatch, local_executor, command)

    result = local_executor.execute(command)
    assert isinstance(result, CommandResult)
    assert result.code == 0
