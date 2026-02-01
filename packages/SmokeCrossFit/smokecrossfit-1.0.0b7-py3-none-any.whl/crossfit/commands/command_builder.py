import copy
import glob
import os.path
from pathlib import Path
from typing import List, Optional, Self, Tuple
from typeguard import typechecked
from crossfit.commands.command import Command


class CommandBuilder:
    """Builder class for constructing Command objects with a fluent interface."""
    _command: Command

    def __init__(self):
        """
        Initializes a new CommandBuilder instance with an empty Command.
        """
        self._command: Command = Command()

    @typechecked()
    def with_next_command(self, command: Command):
        """
        Sets the next command to be executed after the current command.
        :param command: The Command object to be executed next
        """
        self._command.next_command = command

    @typechecked()
    def with_command(self, command: List[str]) -> Self:
        """
        Initializes the command from a list of strings.
        :param command: A list containing at least two strings - execution call and command to execute
        :returns: Self for method chaining
        :raises ValueError: If the command list has fewer than two elements
        """
        if len(command) < 2:
            raise ValueError(
            'Command construct parameter must have at least two str arguments - execution call and any arguments')
        self._command.execution_call = command[0]
        self._command.command_to_execute = command[1]
        self._command.command_body = command[2:]
        return self

    @typechecked()
    def set_execution_call(self, execution_call: str, path: Optional[Path] = None) -> Self:
        """
        Sets the execution call for the command.
        :param execution_call: The executable or interpreter to run
        :param path: Optional path to prepend to the execution call
        :returns: Self for method chaining
        """
        self._command.execution_call = execution_call if path is None else os.path.relpath(path / execution_call)
        return self

    @typechecked()
    def set_command_to_execute(self, command_to_execute: str) -> Self:
        """
        Sets the main command or script to execute.
        :param command_to_execute: The command or script name to execute
        :returns: Self for method chaining
        """
        self._command.command_to_execute = command_to_execute
        return self

    @typechecked()
    def set_command_body(self, command_body: List[str]) -> Self:
        """
        Sets the command body containing arguments and options.
        :param command_body: A list of strings representing the command body
        :returns: Self for method chaining
        """
        self._command.command_body = command_body
        return self

    @typechecked()
    def set_values_delimiter(self, delimiter: Optional[str], update_current_values: bool = False) -> Self:
        """
        Sets the delimiter used between options and their values.
        :param delimiter: The delimiter string (e.g., '=' or ':'), or None for space separation
        :param update_current_values: If True, updates all existing options with the new delimiter
        :returns: Self for method chaining
        """
        if self._command.values_delimiter != delimiter:
            self._command.values_delimiter = delimiter
            if update_current_values:
                self.__update_all_options()
        return self

    @typechecked()
    def add_option(self, option: str, value: Optional[str] = None, delimiter: Optional[str] = None) -> Self:
        """
        Adds a single option to the command.
        :param option: The option flag or name (e.g., '--verbose' or '-v')
        :param value: Optional value for the option
        :param delimiter: Optional delimiter to use for this specific option
        :returns: Self for method chaining
        """
        self.__add_option(option, value, delimiter)
        return self

    @typechecked()
    def add_options(self, *args: Tuple[str, Optional[str]]) -> Self:
        """
        Adds multiple options to the command.
        :param args: Variable number of tuples, each containing (option, value) pairs
        :returns: Self for method chaining
        """
        for option in args:
            self.__add_option(option[0], option[1])
        return self

    @typechecked()
    def add_arguments(self, *args) -> Self:
        """
        Adds positional arguments to the command.
        :param args: Variable number of arguments to add
        :returns: Self for method chaining
        """
        self._command.command_body = self._command.command_body[len(self._command.arguments):]
        self._command.arguments.extend(list(args).copy())
        self._command.command_body = self._command.arguments + self._command.command_body
        return self

    @typechecked()
    def add_path_arguments(self, *paths: Path) -> Self:
        """
        Adds path arguments to the command, resolving glob patterns.
        :param paths: Variable number of Path objects, which may contain glob patterns
        :returns: Self for method chaining
        :raises FileNotFoundError: If a path does not exist and is not a valid glob pattern
        """
        [self._command.validate_path(path) for path in paths]
        resolved_glob_paths = []
        for path in paths:
            resolved_glob_paths.extend(
                os.path.relpath(resolved_path) for resolved_path in glob.glob(str(path), recursive=True))
        self.add_arguments(*[os.path.relpath(path) for path in resolved_glob_paths])
        return self

    def build_command(self) -> Command:
        """
        Builds and returns a copy of the configured Command object.
        :returns: A copy of the Command object with all configured settings
        """
        return copy.copy(self._command)

    def __update_all_options(self) -> Self:
        """
        Updates all existing options with the current delimiter.
        :returns: Self for method chaining
        """
        self._command.command_body = self._command.command_body[:-sum(len(option) for option in self._command.options)]
        options = self._command.options.copy()
        self._command.options = []
        self.add_options(*options)
        return self

    def __add_option(self, option: str, value: Optional[str] = None, delimiter: Optional[str] = None) -> Self:
        """
        Internal method to add an option to the command body.
        :param option: The option flag or name
        :param value: Optional value for the option
        :param delimiter: Optional delimiter to override the default
        :returns: Self for method chaining
        """
        if delimiter is not None:
            self._command.values_delimiter = delimiter

        if value is not None:
            if self._command.values_delimiter is not None:
                self._command.command_body.append(f"{option}{self._command.values_delimiter}{value}")
            else:
                self._command.command_body.extend([option, value])
        else:
            self._command.command_body.append(option)
        self._command.options.append((option, value))
