# test_executor.py
import pytest

from crossfit.commands.command import Command
from crossfit.executors.executor import Executor
from crossfit.models.command_models import CommandResult


class ConcreteExecutor(Executor):
    """Concrete implementation of Executor for testing purposes."""

    def __init__(self, logger, catch: bool = True, results: list = None):
        """
        :param logger: Logger instance
        :param catch: Whether to catch exceptions
        :param results: List of CommandResult objects to return in sequence
        """
        super().__init__(logger, catch)
        self._results = results or []
        self._call_count = 0
        self._executed_commands = []

    def _execute_single(self, command: Command) -> CommandResult:
        """Returns pre-configured results in sequence."""
        self._executed_commands.append(command)
        if self._call_count < len(self._results):
            result = self._results[self._call_count]
            self._call_count += 1
            return result
        # Default success result
        return CommandResult(code=0, command=str(command), output="success", error="")


@pytest.fixture
def success_result():
    """Fixture for a successful CommandResult."""
    return CommandResult(code=0, command="test-cmd", output="success output", error="")


@pytest.fixture
def failure_result():
    """Fixture for a failed CommandResult."""
    return CommandResult(code=1, command="test-cmd", output="", error="error occurred")


@pytest.fixture
def simple_command():
    """Fixture for a simple Command without chaining."""
    cmd = Command()
    cmd.execution_call = "echo"
    cmd.command_to_execute = "hello"
    return cmd


@pytest.fixture
def chained_commands():
    """Fixture for a chain of 3 commands."""
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

    return cmd1, cmd2, cmd3


class TestExecutorInit:
    """Tests for Executor initialization."""

    def test_executor_init_with_defaults(self, logger):
        """Test Executor initialization with default catch=True."""
        executor = ConcreteExecutor(logger=logger)
        assert executor._logger == logger
        assert executor._catch is True

    def test_executor_init_with_catch_false(self, logger):
        """Test Executor initialization with catch=False."""
        executor = ConcreteExecutor(logger=logger, catch=False)
        assert executor._catch is False


class TestExecuteSingle:
    """Tests for single command execution."""

    def test_execute_single_command_success(self, simple_command, success_result, logger):
        """Test executing a single command successfully."""
        executor = ConcreteExecutor(logger=logger, results=[success_result])
        result = executor.execute(simple_command)

        assert result.code == 0
        assert result.output == "success output"
        assert len(executor._executed_commands) == 1

    def test_execute_single_command_failure(self, simple_command, failure_result, logger):
        """Test executing a single command that fails."""
        executor = ConcreteExecutor(logger=logger, results=[failure_result])
        result = executor.execute(simple_command)

        assert result.code == 1
        assert result.error == "error occurred"
        assert len(executor._executed_commands) == 1


class TestExecuteChain:
    """Tests for chained command execution."""

    def test_execute_chain_all_success(self, chained_commands, logger):
        """Test executing a chain of commands where all succeed."""
        cmd1, cmd2, cmd3 = chained_commands
        results = [
            CommandResult(code=0, command="cmd1", output="out1", error=""),
            CommandResult(code=0, command="cmd2", output="out2", error=""),
            CommandResult(code=0, command="cmd3", output="out3", error=""),
        ]
        executor = ConcreteExecutor(logger=logger, results=results)
        executor.execute(cmd1)

        # All 3 commands should be executed
        assert len(executor._executed_commands) == 3
        assert executor._executed_commands[0] is cmd1
        assert executor._executed_commands[1] is cmd2
        assert executor._executed_commands[2] is cmd3

    def test_execute_chain_stops_on_failure(self, chained_commands, logger):
        """Test that chain stops executing when a command fails (with code != 0)."""
        cmd1, cmd2, cmd3 = chained_commands
        results = [
            CommandResult(code=1, command="cmd1", output="", error="cmd1 failed"),  # First fails
            CommandResult(code=0, command="cmd2", output="out2", error=""),
            CommandResult(code=0, command="cmd3", output="out3", error=""),  # Should not be reached
        ]
        executor = ConcreteExecutor(logger=logger, results=results)
        result = executor.execute(cmd1)

        # Only first command should be executed because it failed
        assert len(executor._executed_commands) == 1
        assert result.code != 0  # Should reflect failure

    def test_execute_chain_first_command_fails(self, chained_commands, logger):
        """Test that chain stops immediately if first command fails."""
        cmd1, cmd2, cmd3 = chained_commands
        results = [
            CommandResult(code=127, command="cmd1", output="", error="cmd1 not found"),
        ]
        executor = ConcreteExecutor(logger=logger, results=results)
        result = executor.execute(cmd1)

        # Only first command should be executed
        assert len(executor._executed_commands) == 1
        assert result.code == 127

    def test_execute_chain_aggregates_results(self, chained_commands, logger):
        """Test that results are properly aggregated across the chain."""
        cmd1, cmd2, cmd3 = chained_commands
        results = [
            CommandResult(code=0, command="cmd1 arg1", output="out1", error=""),
            CommandResult(code=0, command="cmd2 arg2", output="out2", error=""),
            CommandResult(code=0, command="cmd3 arg3", output="out3", error=""),
        ]
        executor = ConcreteExecutor(logger=logger, results=results)
        result = executor.execute(cmd1)

        # Check aggregated command string
        assert "cmd1 arg1" in result.command
        assert "cmd2 arg2" in result.command
        assert "cmd3 arg3" in result.command
        # Check aggregated output
        assert "out1" in result.output
        assert "out2" in result.output
        assert "out3" in result.output


class TestExecuteEdgeCases:
    """Tests for edge cases in command execution."""

    def test_execute_command_without_next_command(self, simple_command, success_result, logger):
        """Test executing a command that has no next_command."""
        executor = ConcreteExecutor(logger=logger, results=[success_result])
        result = executor.execute(simple_command)

        assert len(executor._executed_commands) == 1
        assert result.code == 0

    def test_execute_two_command_chain(self, logger):
        """Test executing a chain of exactly 2 commands."""
        cmd1 = Command()
        cmd1.execution_call = "first"
        cmd1.command_to_execute = "cmd"

        cmd2 = Command()
        cmd2.execution_call = "second"
        cmd2.command_to_execute = "cmd"

        cmd1.next_command = cmd2

        results = [
            CommandResult(code=0, command="first cmd", output="first", error=""),
            CommandResult(code=0, command="second cmd", output="second", error=""),
        ]
        executor = ConcreteExecutor(logger=logger, results=results)
        executor.execute(cmd1)

        assert len(executor._executed_commands) == 2

    def test_execute_with_non_zero_code_stops_chain(self, logger):
        """Test that any non-zero return code stops the chain."""
        cmd1 = Command()
        cmd1.execution_call = "cmd1"

        cmd2 = Command()
        cmd2.execution_call = "cmd2"

        cmd1.next_command = cmd2

        # Return code 255 should also stop the chain
        results = [
            CommandResult(code=255, command="cmd1", output="", error="custom error"),
        ]
        executor = ConcreteExecutor(logger=logger, results=results)
        result = executor.execute(cmd1)

        assert len(executor._executed_commands) == 1
        assert result.code == 255
