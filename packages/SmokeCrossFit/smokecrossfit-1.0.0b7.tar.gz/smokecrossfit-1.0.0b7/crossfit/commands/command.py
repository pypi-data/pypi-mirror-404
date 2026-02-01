import copy
import glob
from pathlib import Path
from typing import Optional, List, Tuple, Self
from typeguard import typechecked

COMMAND_DELIMITER = " "


class Command:
    next_command: Optional[Self]
    execution_call: Optional[str]
    command_to_execute: Optional[str]
    command_body: List[str]
    options: List[Tuple[str, Optional[str]]]
    arguments: List[str]
    values_delimiter: Optional[str]

    @typechecked()
    def __init__(self):
        """
        Initializes the command structure
        """
        self.next_command = None
        self.execution_call = None
        self.command_to_execute = None
        self.command_body = []
        self.options = []
        self.arguments = []
        self.values_delimiter = None

    @property
    def command(self) -> List[str]:
        """
        :returns: The command itself as a list of strings
        """
        return list(filter(lambda s: s is not None, [self.execution_call, self.command_to_execute, *self.command_body]))

    @command.setter
    def command(self, value: List[str]):
        """
        Sets the command body from a list of strings
        :param value: The command body as list of strings
        """
        self.options = []
        self.arguments = []
        self.command_body = value

    def __str__(self) -> str:
        """
        :returns: The command itself as a single string
        """
        return COMMAND_DELIMITER.join(self.command)

    def validate(self):
        """
        Validates that the command has an execution call set
        :raises AttributeError: If execution call is not set
        """
        if not self.execution_call:
            raise AttributeError(f"Ensure tool's execution call is set. Valued as: '{self.execution_call}'")

    @staticmethod
    def validate_path(path: Path):
        """
        Validates that the given path exists, supports wildcards
        :param path: The path to validate
        :raises FileNotFoundError: If the path does not exist
        """
        paths = glob.glob(str(path), recursive=True)
        if not paths:
            raise FileNotFoundError(f"Could not recognize given path - '{path}' - does not exist")

    def __copy__(self) -> Self:
        """
        :returns: A shallow copy of the command
        """
        command_copy = Command()
        command_copy.next_command = copy.copy(self.next_command)
        command_copy.execution_call = self.execution_call
        command_copy.command_to_execute = self.command_to_execute
        command_copy.command_body = self.command_body
        command_copy.options = self.options
        command_copy.arguments = self.arguments
        command_copy.values_delimiter = self.values_delimiter
        return command_copy
