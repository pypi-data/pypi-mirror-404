import copy
from pathlib import Path

import pytest

from crossfit import Command


class TestCommand:
    """Tests for the Command class."""

    # region Initialization Tests
    def test_command_init_defaults(self):
        """Test that Command initializes with correct default values."""
        command = Command()
        assert command.execution_call is None
        assert command.command_to_execute is None
        assert command.command_body == []
        assert command.options == []
        assert command.arguments == []
        assert command.values_delimiter is None
        assert command.next_command is None

    def test_command_property_returns_empty_list_when_not_set(self):
        """Test that command property returns empty list when nothing is set."""
        command = Command()
        assert command.command == []

    def test_command_property_returns_correct_list(self):
        """Test that command property returns execution_call, command_to_execute, and command_body."""
        command = Command()
        command.execution_call = "python"
        command.command_to_execute = "run.py"
        command.command_body = ["--verbose", "arg1"]
        assert command.command == ["python", "run.py", "--verbose", "arg1"]

    def test_command_property_filters_none_values(self):
        """Test that command property filters out None values."""
        command = Command()
        command.execution_call = "python"
        command.command_to_execute = None
        command.command_body = ["arg1"]
        assert command.command == ["python", "arg1"]
    # endregion

    # region String Representation Tests
    def test_command_str_empty(self):
        """Test string representation of empty command."""
        command = Command()
        assert str(command) == ""

    def test_command_str_with_values(self):
        """Test string representation of command with values."""
        command = Command()
        command.execution_call = "python"
        command.command_to_execute = "run.py"
        command.command_body = ["--debug"]
        assert str(command) == "python run.py --debug"
    # endregion

    # region Validation Tests
    def test_command_validate_without_execution_call(self):
        """Test that validate raises AttributeError when execution_call is not set."""
        command = Command()
        with pytest.raises(AttributeError):
            command.validate()

    def test_command_validate_with_execution_call(self):
        """Test that validate passes when execution_call is set."""
        command = Command()
        command.execution_call = "python"
        command.validate()  # Should not raise
    # endregion

    # region Path Validation Tests
    def test_validate_path_with_valid_file(self, tests_dir_path):
        """Test validate_path with an existing file."""
        valid_path = tests_dir_path / "helpers/command/f1.txt"
        Command.validate_path(valid_path)  # Should not raise

    def test_validate_path_with_valid_directory(self, tests_dir_path):
        """Test validate_path with an existing directory."""
        valid_path = tests_dir_path / "helpers/command/"
        Command.validate_path(valid_path)  # Should not raise

    def test_validate_path_with_invalid_path(self):
        """Test validate_path raises FileNotFoundError for non-existent path."""
        invalid_path = Path("non_existent_path/file.txt")
        with pytest.raises(FileNotFoundError):
            Command.validate_path(invalid_path)

    def test_validate_path_with_glob_pattern(self, tests_dir_path):
        """Test validate_path with glob pattern."""
        glob_path = tests_dir_path / "helpers/command/*.txt"
        Command.validate_path(glob_path)  # Should not raise
    # endregion

    # region Copy Tests
    def test_command_copy(self):
        """Test that __copy__ creates a proper shallow copy."""
        original = Command()
        original.execution_call = "python"
        original.command_to_execute = "run.py"
        original.command_body = ["--verbose"]
        original.options = [("--verbose", None)]
        original.arguments = ["arg1"]
        original.values_delimiter = "="

        copied = copy.copy(original)

        assert copied.execution_call == original.execution_call
        assert copied.command_to_execute == original.command_to_execute
        assert copied.command_body == original.command_body
        assert copied.options == original.options
        assert copied.arguments == original.arguments
        assert copied.values_delimiter == original.values_delimiter
        assert copied is not original

    def test_command_copy_with_next_command(self):
        """Test that __copy__ copies next_command."""
        next_cmd = Command()
        next_cmd.execution_call = "echo"
        next_cmd.command_to_execute = "done"

        original = Command()
        original.execution_call = "python"
        original.command_to_execute = "run.py"
        original.next_command = next_cmd

        copied = copy.copy(original)

        assert copied.next_command is not None
        assert copied.next_command.execution_call == "echo"
    # endregion

    # region Command Setter Tests
    def test_command_setter_resets_options_and_arguments(self):
        """Test that setting command resets options and arguments."""
        command = Command()
        command.options = [("--opt", "val")]
        command.arguments = ["arg1"]
        command.command = ["new", "body"]

        assert command.options == []
        assert command.arguments == []
        assert command.command_body == ["new", "body"]
    # endregion
