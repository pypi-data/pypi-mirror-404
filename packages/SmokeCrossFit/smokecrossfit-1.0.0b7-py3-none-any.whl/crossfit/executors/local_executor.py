import subprocess
from logging import Logger
import shlex
from crossfit.commands.command import Command
from crossfit.executors.executor import Executor
from crossfit.models.command_models import CommandResult


class LocalExecutor(Executor):
    """Executor that runs commands locally via subprocess."""

    def __init__(self, logger: Logger, catch: bool = True, **execution_kwargs):
        """
        :param logger: Logger instance for logging execution details (required)
        :param catch: If True, catches exceptions and returns error in CommandResult.
                      If False, re-raises exceptions.
        :param execution_kwargs: Additional arguments passed to subprocess.run
        """
        super().__init__(logger, catch)
        self._exec_kwargs = {
            "capture_output": True,
            "check": True,
            "text": True,
        }
        self._exec_kwargs.update(execution_kwargs)

    def _execute_single(self, command: Command) -> CommandResult:
        """
        Executes a single command without handling chained commands.
        :param command: The Command object to execute
        :returns: CommandResult with execution details
        """
        command_str = str(command)
        try:
            command.validate()
            res = subprocess.run(shlex.split(command_str), **self._exec_kwargs)

            if res.returncode != 0 or (res.stderr and len(res.stderr)):
                raise subprocess.CalledProcessError(
                    res.returncode, command_str, output=res.stdout, stderr=res.stderr
                )

            self._logger.info(f"Command '{command_str}' finished with exit code {res.returncode}. {res.stdout}")
            return CommandResult(
                code=res.returncode,
                command=command_str,
                output=res.stdout,
                error=res.stderr,
            )

        except subprocess.CalledProcessError as cpe:
            self._logger.error(
                f"Execution of command '{command_str}' failed with error: {cpe.stderr}. Return code {cpe.returncode}."
            )
            if not self._catch:
                raise
            return CommandResult(
                code=cpe.returncode,
                command=command_str,
                output=cpe.stdout or "",
                error=cpe.stderr or "",
            )

        except FileNotFoundError as not_found_e:
            self._logger.error(f"Command '{command_str}' not found. {not_found_e.strerror}")
            if not self._catch:
                raise
            return CommandResult(
                code=124,
                command=command_str,
                output="",
                error=not_found_e.strerror,
            )

        except AttributeError as attr_e:
            self._logger.error(f"Command validation failed: {attr_e}")
            if not self._catch:
                raise
            return CommandResult(
                code=1,
                command=command_str,
                output="",
                error=str(attr_e),
            )

        except Exception as e:
            self._logger.error(f"An error occurred while executing command '{command_str}': {e}")
            if not self._catch:
                raise
            return CommandResult(
                code=1,
                command=command_str,
                output="",
                error=str(e),
            )
