from abc import ABC, abstractmethod
from logging import Logger

from crossfit.commands.command import Command
from crossfit.models.command_models import CommandResult


class Executor(ABC):
    """Abstract base class for command executors."""

    def __init__(self, logger: Logger, catch: bool = True):
        """
        :param logger: Logger instance for logging execution details (required)
        :param catch: If True, catches exceptions and returns error in CommandResult.
                      If False, re-raises exceptions.
        """
        self._logger = logger
        self._catch = catch

    def execute(self, command: Command) -> CommandResult:
        """
        Executes the given command and any chained commands via next_command.
        :param command: The Command object to execute
        :returns: Aggregated CommandResult from all executed commands
        """
        result = self._execute_single(command)

        current = command.next_command
        while current is not None:
            if result.code != 0:
                self._logger.warning(f"Stopping command chain due to failure. Code: {result.code}")
                break
            next_result = self._execute_single(current)
            result = result.add_result(next_result)
            current = current.next_command

        return result

    @abstractmethod
    def _execute_single(self, command: Command) -> CommandResult:
        """
        Executes a single command without handling chained commands.
        :param command: The Command object to execute
        :returns: CommandResult with execution details
        """
        raise NotImplementedError
