# test_local_executor.py
import subprocess
import pytest
from crossfit.commands.command import Command
from crossfit.executors.local_executor import LocalExecutor
from crossfit.models.command_models import CommandResult


@pytest.fixture
def executor(logger):
    """Fixture for LocalExecutor with catch=True (default)."""
    return LocalExecutor(logger=logger, catch=True)


@pytest.fixture
def executor_no_catch(logger):
    """Fixture for LocalExecutor with catch=False."""
    return LocalExecutor(logger=logger, catch=False)


@pytest.fixture
def simple_command():
    """Fixture for a simple valid command."""
    cmd = Command()
    cmd.execution_call = "echo"
    cmd.command_to_execute = "hello"
    return cmd


@pytest.fixture
def invalid_command():
    """Fixture for an invalid command (no execution_call)."""
    cmd = Command()
    cmd.command_to_execute = "test"
    return cmd


@pytest.fixture
def nonexistent_command():
    """Fixture for a command with non-existent executable."""
    cmd = Command()
    cmd.execution_call = "nonexistent_tool_xyz"
    cmd.command_to_execute = "arg"
    return cmd


class TestLocalExecutorInit:
    """Tests for LocalExecutor initialization."""

    def test_init_with_defaults(self, logger):
        """Test LocalExecutor initialization with default values."""
        executor = LocalExecutor(logger=logger)
        assert executor._logger == logger
        assert executor._catch is True
        assert executor._exec_kwargs["capture_output"] is True
        assert executor._exec_kwargs["check"] is True
        assert executor._exec_kwargs["text"] is True

    def test_init_with_catch_false(self, logger):
        """Test LocalExecutor initialization with catch=False."""
        executor = LocalExecutor(logger=logger, catch=False)
        assert executor._catch is False

    def test_init_with_custom_kwargs(self, logger):
        """Test LocalExecutor initialization with custom execution kwargs."""
        executor = LocalExecutor(logger=logger, timeout=30, cwd="/tmp")
        assert executor._exec_kwargs["timeout"] == 30
        assert executor._exec_kwargs["cwd"] == "/tmp"

    def test_init_overrides_default_kwargs(self, logger):
        """Test that custom kwargs override defaults."""
        executor = LocalExecutor(logger=logger, capture_output=False, shell=True)
        assert executor._exec_kwargs["capture_output"] is False
        assert executor._exec_kwargs["shell"] is True


class TestLocalExecutorSuccess:
    """Tests for successful command execution."""

    def test_execute_success(self, executor, simple_command, monkeypatch):
        """Test successful command execution."""

        def mock_run(cmd, **kwargs):
            return subprocess.CompletedProcess(cmd, returncode=0, stdout="hello", stderr="")

        monkeypatch.setattr(subprocess, "run", mock_run)
        result = executor.execute(simple_command)

        assert result.code == 0
        assert result.output == "hello"
        assert result.error == ""

    def test_execute_returns_command_result(self, executor, simple_command, monkeypatch):
        """Test that execute returns a CommandResult instance."""

        def mock_run(cmd, **kwargs):
            return subprocess.CompletedProcess(cmd, returncode=0, stdout="", stderr="")

        monkeypatch.setattr(subprocess, "run", mock_run)
        result = executor.execute(simple_command)

        assert isinstance(result, CommandResult)

    def test_execute_includes_command_string(self, executor, simple_command, monkeypatch):
        """Test that result includes the command string."""

        def mock_run(cmd, **kwargs):
            return subprocess.CompletedProcess(cmd, returncode=0, stdout="", stderr="")

        monkeypatch.setattr(subprocess, "run", mock_run)
        result = executor.execute(simple_command)

        assert "echo" in result.command
        assert "hello" in result.command


class TestLocalExecutorFailure:
    """Tests for failed command execution."""

    def test_execute_nonzero_return_code_catch_true(self, executor, simple_command, monkeypatch):
        """Test execution with non-zero return code when catch=True."""

        def mock_run(cmd, **kwargs):
            return subprocess.CompletedProcess(cmd, returncode=1, stdout="", stderr="error msg")

        monkeypatch.setattr(subprocess, "run", mock_run)
        result = executor.execute(simple_command)

        assert result.code == 1
        assert "error msg" in result.error

    def test_execute_nonzero_return_code_catch_false(self, executor_no_catch, simple_command, monkeypatch):
        """Test execution with non-zero return code when catch=False raises exception."""

        def mock_run(cmd, **kwargs):
            return subprocess.CompletedProcess(cmd, returncode=1, stdout="", stderr="error msg")

        monkeypatch.setattr(subprocess, "run", mock_run)

        with pytest.raises(subprocess.CalledProcessError):
            executor_no_catch.execute(simple_command)

    def test_execute_with_stderr_only_catch_true(self, executor, simple_command, monkeypatch):
        """Test execution with stderr even when return code is 0 (catch=True)."""

        def mock_run(cmd, **kwargs):
            return subprocess.CompletedProcess(cmd, returncode=0, stdout="", stderr="warning message")

        monkeypatch.setattr(subprocess, "run", mock_run)
        result = executor.execute(simple_command)

        # Should be treated as failure due to stderr
        assert result.code == 0  # CalledProcessError preserves original code
        assert "warning message" in result.error

    def test_execute_with_stderr_only_catch_false(self, executor_no_catch, simple_command, monkeypatch):
        """Test execution with stderr raises when catch=False."""

        def mock_run(cmd, **kwargs):
            return subprocess.CompletedProcess(cmd, returncode=0, stdout="", stderr="warning message")

        monkeypatch.setattr(subprocess, "run", mock_run)

        with pytest.raises(subprocess.CalledProcessError):
            executor_no_catch.execute(simple_command)


class TestLocalExecutorFileNotFound:
    """Tests for FileNotFoundError handling."""

    def test_execute_file_not_found_catch_true(self, executor, nonexistent_command, monkeypatch):
        """Test FileNotFoundError handling when catch=True."""

        def mock_run(cmd, **kwargs):
            raise FileNotFoundError(2, "No such file or directory")

        monkeypatch.setattr(subprocess, "run", mock_run)
        result = executor.execute(nonexistent_command)

        assert result.code == 124  # Code for file not found
        assert "No such file or directory" in result.error

    def test_execute_file_not_found_catch_false(self, executor_no_catch, nonexistent_command, monkeypatch):
        """Test FileNotFoundError re-raised when catch=False."""

        def mock_run(cmd, **kwargs):
            raise FileNotFoundError(2, "No such file or directory")

        monkeypatch.setattr(subprocess, "run", mock_run)

        with pytest.raises(FileNotFoundError):
            executor_no_catch.execute(nonexistent_command)


class TestLocalExecutorValidation:
    """Tests for command validation."""

    def test_execute_invalid_command_catch_true(self, executor, invalid_command):
        """Test executing invalid command (no execution_call) with catch=True."""
        result = executor.execute(invalid_command)

        assert result.code == 1
        assert "execution call" in result.error.lower() or "attributeerror" in result.error.lower()

    def test_execute_invalid_command_catch_false(self, executor_no_catch, invalid_command):
        """Test executing invalid command raises AttributeError when catch=False."""
        with pytest.raises(AttributeError):
            executor_no_catch.execute(invalid_command)


class TestLocalExecutorCalledProcessError:
    """Tests for CalledProcessError handling."""

    def test_called_process_error_catch_true(self, executor, simple_command, monkeypatch):
        """Test CalledProcessError handling when catch=True."""

        def mock_run(cmd, **kwargs):
            raise subprocess.CalledProcessError(127, cmd, output="", stderr="command not found")

        monkeypatch.setattr(subprocess, "run", mock_run)
        result = executor.execute(simple_command)

        assert result.code == 127
        assert "command not found" in result.error

    def test_called_process_error_catch_false(self, executor_no_catch, simple_command, monkeypatch):
        """Test CalledProcessError re-raised when catch=False."""

        def mock_run(cmd, **kwargs):
            raise subprocess.CalledProcessError(127, cmd, output="", stderr="command not found")

        monkeypatch.setattr(subprocess, "run", mock_run)

        with pytest.raises(subprocess.CalledProcessError) as exc_info:
            executor_no_catch.execute(simple_command)

        assert exc_info.value.returncode == 127


class TestLocalExecutorGenericException:
    """Tests for generic exception handling."""

    def test_generic_exception_catch_true(self, executor, simple_command, monkeypatch):
        """Test generic exception handling when catch=True."""

        def mock_run(cmd, **kwargs):
            raise RuntimeError("unexpected error")

        monkeypatch.setattr(subprocess, "run", mock_run)
        result = executor.execute(simple_command)

        assert result.code == 1
        assert "unexpected error" in result.error

    def test_generic_exception_catch_false(self, executor_no_catch, simple_command, monkeypatch):
        """Test generic exception re-raised when catch=False."""

        def mock_run(cmd, **kwargs):
            raise RuntimeError("unexpected error")

        monkeypatch.setattr(subprocess, "run", mock_run)

        with pytest.raises(RuntimeError):
            executor_no_catch.execute(simple_command)


class TestLocalExecutorChaining:
    """Tests for command chaining with LocalExecutor."""

    def test_execute_chained_commands_all_success(self, executor, monkeypatch):
        """Test executing chained commands where all succeed."""
        cmd1 = Command()
        cmd1.execution_call = "cmd1"
        cmd1.command_to_execute = "arg1"

        cmd2 = Command()
        cmd2.execution_call = "cmd2"
        cmd2.command_to_execute = "arg2"

        cmd1.next_command = cmd2

        call_count = {"count": 0}

        def mock_run(cmd, **kwargs):
            call_count["count"] += 1
            return subprocess.CompletedProcess(cmd, returncode=0, stdout=f"output{call_count['count']}", stderr="")

        monkeypatch.setattr(subprocess, "run", mock_run)
        result = executor.execute(cmd1)

        assert call_count["count"] == 2
        assert result.code == 0
        assert "output1" in result.output
        assert "output2" in result.output

    def test_execute_chained_commands_first_fails(self, executor, monkeypatch):
        """Test that chain stops when first command fails.

        When the first command fails with non-zero code, the chain correctly stops
        because result.code != 0 check happens before executing subsequent commands.
        """
        cmd1 = Command()
        cmd1.execution_call = "cmd1"
        cmd1.command_to_execute = "arg1"

        cmd2 = Command()
        cmd2.execution_call = "cmd2"
        cmd2.command_to_execute = "arg2"

        cmd1.next_command = cmd2

        call_count = {"count": 0}

        def mock_run(cmd, **kwargs):
            call_count["count"] += 1
            # First command fails
            return subprocess.CompletedProcess(cmd, returncode=1, stdout="", stderr="first failed")

        monkeypatch.setattr(subprocess, "run", mock_run)
        result = executor.execute(cmd1)

        # Only first command should be executed
        assert call_count["count"] == 1
        assert result.code == 1

    def test_execute_chained_commands_second_fails(self, executor, monkeypatch):
        """Test chain behavior when second command fails.

        Note: Due to the CommandResult.__add__ using bitwise AND for codes,
        when the first succeeds (code=0) and second fails (code=1), the combined
        code becomes 0 & 1 = 0. This causes the chain to continue executing.
        This test documents the current behavior.
        """
        cmd1 = Command()
        cmd1.execution_call = "cmd1"
        cmd1.command_to_execute = "arg1"

        cmd2 = Command()
        cmd2.execution_call = "cmd2"
        cmd2.command_to_execute = "arg2"

        cmd3 = Command()
        cmd3.execution_call = "cmd3"
        cmd3.command_to_execute = "arg3"

        cmd1.next_command = cmd2
        cmd2.next_command = cmd3

        call_count = {"count": 0}

        def mock_run(cmd, **kwargs):
            call_count["count"] += 1
            if call_count["count"] == 2:
                return subprocess.CompletedProcess(cmd, returncode=1, stdout="", stderr="second failed")
            return subprocess.CompletedProcess(cmd, returncode=0, stdout=f"output{call_count['count']}", stderr="")

        monkeypatch.setattr(subprocess, "run", mock_run)
        executor.execute(cmd1)

        # Due to bitwise AND in CommandResult.__add__, all commands are executed
        # because 0 & 1 = 0, so result.code stays 0 after second command
        assert call_count["count"] == 3  # All commands executed due to current implementation


class TestLocalExecutorKwargs:
    """Tests for execution kwargs handling."""

    def test_kwargs_passed_to_subprocess(self, monkeypatch, logger):
        """Test that execution kwargs are passed to subprocess.run."""
        executor = LocalExecutor(logger=logger, shell=True, timeout=60)

        cmd = Command()
        cmd.execution_call = "echo"
        cmd.command_to_execute = "test"

        received_kwargs = {}

        def mock_run(cmd, **kwargs):
            received_kwargs.update(kwargs)
            return subprocess.CompletedProcess(cmd, returncode=0, stdout="", stderr="")

        monkeypatch.setattr(subprocess, "run", mock_run)
        executor.execute(cmd)

        assert received_kwargs["shell"] is True
        assert received_kwargs["timeout"] == 60
        assert received_kwargs["capture_output"] is True
        assert received_kwargs["check"] is True
        assert received_kwargs["text"] is True
