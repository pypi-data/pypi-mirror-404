import os.path
from pathlib import Path
import pytest
from typeguard import TypeCheckError
from crossfit import Command
from crossfit.commands.command_builder import CommandBuilder


class TestCommandBuilder:
    """Tests for the CommandBuilder class."""

    # region Initialization Tests
    def test_builder_init_without_args(self):
        """Test that CommandBuilder initializes with empty command."""
        command_builder = CommandBuilder()
        command = command_builder.build_command()
        assert command.command == []

    def test_builder_with_command_str(self):
        """Test command string representation after building."""
        command_builder = CommandBuilder().with_command(["python", "run.py"])
        command = command_builder.build_command()
        assert str(command) == "python run.py"
    # endregion

    # region with_command Tests
    @pytest.mark.parametrize("args, expected_execution_call, expected_command_to_execute", [
        (["python", "run.py"], "python", "run.py"),
        (["java", "JarFile.jar"], "java", "JarFile.jar"),
        (["node", "index.js"], "node", "index.js"),
    ], ids=["python", "java", "node"])
    def test_with_command_valid_args(self, args, expected_execution_call, expected_command_to_execute):
        """Test with_command with valid arguments."""
        command_builder = CommandBuilder().with_command(args)
        command = command_builder.build_command()
        assert command.execution_call == expected_execution_call
        assert command.command_to_execute == expected_command_to_execute

    @pytest.mark.parametrize("args", [
        (["python"]),
        (["java", None]),
        ([None, "run.py"]),
    ], ids=["single_arg", "none_value", "execution_call_none"])
    def test_with_command_invalid_args(self, args):
        """Test with_command raises exception for invalid arguments."""
        try:
            CommandBuilder().with_command(args)
        except Exception as err:
            assert isinstance(err, (ValueError, TypeCheckError))

    def test_with_command_extracts_command_body(self):
        """Test that with_command extracts command_body from args after first two."""
        command_builder = CommandBuilder().with_command(["python", "run.py", "arg1", "arg2"])
        command = command_builder.build_command()
        assert command.command_body == ["arg1", "arg2"]
    # endregion

    # region set_execution_call and set_command_to_execute Tests
    def test_set_execution_call_and_command_to_execute(self):
        """Test setting execution call and command to execute separately."""
        command_builder = CommandBuilder().set_execution_call("python").set_command_to_execute("run.py")
        command = command_builder.build_command()
        assert command.execution_call == "python"
        assert command.command_to_execute == "run.py"

    def test_set_execution_call_with_path(self):
        """Test setting execution call with a path parameter."""
        command_builder = CommandBuilder().set_execution_call("python", Path("/usr/bin"))
        command = command_builder.build_command()
        assert "python" in command.execution_call

    def test_validate_without_command_to_execute(self):
        """Test that validation fails when only command_to_execute is set."""
        command_builder = CommandBuilder().set_command_to_execute("python")
        command = command_builder.build_command()
        with pytest.raises(AttributeError):
            command.validate()
    # endregion

    # region set_command_body Tests
    def test_set_command_body(self):
        """Test setting command body directly."""
        command_builder = (CommandBuilder()
                           .set_execution_call("python")
                           .set_command_to_execute("run.py")
                           .set_command_body(["--verbose", "arg1"]))
        command = command_builder.build_command()
        assert command.command_body == ["--verbose", "arg1"]
    # endregion

    # region add_option Tests
    @pytest.mark.parametrize("option, value, expected_command", [
        ("--debug", None, ["python", "run.py", "--debug"]),
        ("--debug", "True", ["python", "run.py", "--debug", "True"]),
        ("--verbose", None, ["python", "run.py", "--verbose"]),
    ], ids=["option_only", "option_value", "another_option"])
    def test_add_option(self, option, value, expected_command):
        """Test adding a single option."""
        command_builder = CommandBuilder().with_command(["python", "run.py"]).add_option(option, value)
        command = command_builder.build_command()
        assert command.command == expected_command

    def test_add_option_with_delimiter(self):
        """Test adding option with custom delimiter."""
        command_builder = CommandBuilder().with_command(["python", "run.py"]).add_option("--opt", "val", "=")
        command = command_builder.build_command()
        assert command.command == ["python", "run.py", "--opt=val"]
    # endregion

    # region add_options Tests
    @pytest.mark.parametrize("options, expected_command", [
        ([("--debug", None), ("--verbose", None)], ["python", "run.py", "--debug", "--verbose"]),
        ([("--debug", None), ("--verbose", None), ("--option1", "value1"), ("--option2", "value2")],
         ["python", "run.py", "--debug", "--verbose", "--option1", "value1", "--option2", "value2"]),
    ], ids=["options_only", "options_kwargs"])
    def test_add_options(self, options, expected_command):
        """Test adding multiple options at once."""
        command_builder = CommandBuilder().with_command(["python", "run.py"]).add_options(*options)
        command = command_builder.build_command()
        assert command.command == expected_command
    # endregion

    # region add_arguments Tests
    @pytest.mark.parametrize("args, expected_command", [
        (["arg1", "arg2"], ["python", "run.py", "arg1", "arg2"]),
        (["arg3", "arg4"], ["python", "run.py", "arg3", "arg4"]),
    ], ids=["two_args", "another_two_args"])
    def test_add_arguments(self, args, expected_command):
        """Test adding positional arguments."""
        command_builder = CommandBuilder().with_command(["python", "run.py"]).add_arguments(*args)
        command = command_builder.build_command()
        assert command.command == expected_command

    def test_add_consecutive_arguments(self):
        """Test adding multiple consecutive arguments."""
        command_builder = CommandBuilder().with_command(["python", "run.py"]).add_arguments("arg1", "arg2", "arg3")
        command = command_builder.build_command()
        assert command.command == ["python", "run.py", "arg1", "arg2", "arg3"]
    # endregion

    # region add_path_arguments Tests
    def test_add_path_arguments(self, tests_dir_path):
        """Test adding path arguments."""
        expected_command = ["python", "run.py", os.path.relpath(tests_dir_path / r"helpers/command/f1.txt"),
                            os.path.relpath(tests_dir_path / r"helpers/command/")]
        paths = [tests_dir_path / r"helpers/command/f1.txt", tests_dir_path / r"helpers/command/"]
        command_builder = CommandBuilder().with_command(["python", "run.py"]).add_path_arguments(*paths)
        command = command_builder.build_command()
        assert command.command == expected_command

    def test_add_path_arguments_with_absolute_paths(self, tests_dir_path):
        """Test adding absolute path arguments."""
        command_builder = CommandBuilder().with_command(["python", "run.py"]).add_path_arguments(
            tests_dir_path / "helpers/command/", tests_dir_path / "helpers/command/f1.txt")
        command = command_builder.build_command()
        assert command.command == ["python", "run.py", os.path.relpath(tests_dir_path / "helpers/command/"),
                                   os.path.relpath(tests_dir_path / "helpers/command/f1.txt")]

    def test_add_invalid_path_arguments(self):
        """Test that invalid path raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            paths = ["test_helpers/command/f5"]
            CommandBuilder().with_command(["python", "run.py"]).add_path_arguments(Path(*paths))
    # endregion

    # region set_values_delimiter Tests
    def test_set_values_delimiter(self):
        """Test setting and updating values delimiter."""
        command_builder = CommandBuilder().with_command(["python", "run.py"]).add_option("--option", "value1", "=")
        command = command_builder.build_command()
        assert command.command == ["python", "run.py", "--option=value1"]
        command = command_builder.set_values_delimiter(",", True).build_command()
        assert command.command == ["python", "run.py", "--option,value1"]

    def test_set_values_delimiter_to_none(self):
        """Test setting delimiter to None removes delimiter."""
        command_builder = CommandBuilder().with_command(["python", "run.py"]).add_option("--option", "value1", "=")
        command = command_builder.build_command()
        assert command.command == ["python", "run.py", "--option=value1"]
        command = command_builder.set_values_delimiter(None, True).build_command()
        assert command.command == ["python", "run.py", "--option", "value1"]

    def test_set_values_delimiter_to_none_with_option_without_value(self):
        """Test setting delimiter to None when some options have no value."""
        command_executors = ["python", "run.py"]
        opt1 = ("--option", "value1")
        opt2 = ("--banana", None)
        command_builder = CommandBuilder().with_command(command_executors).add_option(opt1[0], opt1[1], "=").add_option(opt2[0], opt2[1])
        command = command_builder.build_command()
        assert command.command == ["python", "run.py", "--option=value1", "--banana"]
        command = command_builder.set_values_delimiter(None, True).build_command()
        assert (" ".join(command_executors) in str(command) and " ".join(opt1) in str(command)
                and "--banana" in command.command)

    def test_set_values_delimiter_with_no_previous_delimiter(self):
        """Test setting delimiter when no delimiter was set before."""
        command_builder = CommandBuilder().with_command(["python", "run.py"]).add_option("--option", "value1")
        command = command_builder.build_command()
        assert command.command == ["python", "run.py", "--option", "value1"]
        command = command_builder.set_values_delimiter(",", True).build_command()
        assert command.command == ["python", "run.py", "--option,value1"]

    def test_update_values_delimiter_with_existing_options(self):
        """Test updating delimiter updates all existing options."""
        command_builder = (CommandBuilder().with_command(["python", "run.py"])
                           .add_option("--option1", "value1", "=").add_option("--option2", "value2", "="))
        command = command_builder.build_command()
        assert command.command == ["python", "run.py", "--option1=value1", "--option2=value2"]
        command = command_builder.set_values_delimiter(",", True).build_command()
        assert command.command == ["python", "run.py", "--option1,value1", "--option2,value2"]
        command = command_builder.add_option("--option3", "value3").build_command()
        assert command.command == ["python", "run.py", "--option1,value1", "--option2,value2", "--option3,value3"]

    def test_invalid_values_delimiter_type(self):
        """Test that invalid delimiter type raises TypeCheckError."""
        command_builder = (CommandBuilder().with_command(["python", "run.py"]))
        with pytest.raises(TypeCheckError):
            command_builder.set_values_delimiter(123)

    def test_set_delimiter_without_updating_previous(self):
        """Test setting new delimiter without changing previous options."""
        command_builder = ((CommandBuilder().with_command(["python", "run.py"]))
                           .add_option("--option1", "value1").add_option("--option2", "value2"))
        command = command_builder.build_command()
        assert command.command == ["python", "run.py", "--option1", "value1", "--option2", "value2"]
        command_builder = command_builder.set_values_delimiter("=").add_option("--option3", "value3")
        command = command_builder.build_command()
        assert command.command == ["python", "run.py", "--option1", "value1", "--option2", "value2", "--option3=value3"]

    def test_set_delimiter_then_add_option(self):
        """Test adding option after setting delimiter."""
        command_builder = ((CommandBuilder().with_command(["python", "run.py"]))
                           .add_option("--option1", "value1").add_option("--option2", "value2"))
        command = command_builder.build_command()
        assert command.command == ["python", "run.py", "--option1", "value1", "--option2", "value2"]
        command_builder = command_builder.set_values_delimiter("=", True).add_option("--option3", "value3")
        command = command_builder.build_command()
        assert command.command == ["python", "run.py", "--option1=value1", "--option2=value2", "--option3=value3"]
    # endregion

    # region Ordering Tests
    def test_order_of_arguments_and_options(self):
        """Test that arguments and options maintain correct order."""
        command_builder = (CommandBuilder().with_command(["python", "run.py"])
                           .add_arguments("arg1", "arg2").add_option("--option", "value"))
        command = command_builder.build_command()
        assert command.command == ["python", "run.py", "arg1", "arg2", "--option", "value"]
        command_builder = command_builder.add_arguments("arg3", "arg4").add_option("--option2", "value2")
        command = command_builder.build_command()
        assert command.command == ["python", "run.py", "arg1", "arg2", "arg3", "arg4", "--option", "value", "--option2", "value2"]

    def test_order_with_blank_arguments(self):
        """Test ordering when adding empty arguments."""
        command_builder = (CommandBuilder().with_command(["python", "run.py"])
                           .add_arguments().add_option("--option", "value"))
        command = command_builder.build_command()
        assert command.command == ["python", "run.py", "--option", "value"]
        command_builder = command_builder.add_arguments("arg3", "arg4").add_option("--option2", "value2")
        command = command_builder.build_command()
        assert command.command == ["python", "run.py", "arg3", "arg4", "--option", "value", "--option2", "value2"]
    # endregion

    # region build_command Tests
    def test_build_command_returns_copy(self):
        """Test that build_command returns a copy, not the original."""
        command_builder = CommandBuilder().with_command(["python", "run.py"])
        command1 = command_builder.build_command()
        command2 = command_builder.build_command()
        assert command1 is not command2

    def test_build_command_modifications_do_not_affect_builder(self):
        """Test that modifying built command doesn't affect builder."""
        command_builder = CommandBuilder().with_command(["python", "run.py"])
        command = command_builder.build_command()
        command.execution_call = "java"

        new_command = command_builder.build_command()
        assert new_command.execution_call == "python"
    # endregion

    # region with_next_command Tests
    def test_with_next_command(self):
        """Test setting next command for chaining."""
        next_cmd = Command()
        next_cmd.execution_call = "echo"
        next_cmd.command_to_execute = "done"

        command_builder = CommandBuilder().with_command(["python", "run.py"])
        command_builder.with_next_command(next_cmd)
        command = command_builder.build_command()

        assert command.next_command is not None
        assert command.next_command.execution_call == "echo"
        assert command.next_command.command_to_execute == "done"
    # endregion

    # region Method Chaining Tests
    def test_method_chaining(self):
        """Test that all builder methods support chaining."""
        command = (CommandBuilder()
                   .with_command(["python", "run.py"])
                   .add_option("--verbose", None)
                   .add_option("--output", "file.txt", "=")
                   .add_arguments("input.txt")
                   .set_values_delimiter(":")
                   .build_command())

        assert command.execution_call == "python"
        assert command.command_to_execute == "run.py"
        assert "--verbose" in command.command
        assert "--output=file.txt" in command.command
        assert "input.txt" in command.command
    # endregion
