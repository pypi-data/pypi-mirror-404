# CrossFit Coverage Tools

CrossFit is a Python package designed to provide a unified interface for various code coverage tools. It wraps the functionality of different coverage CLI tools, allowing developers to use a consistent API regardless of which underlying tool they prefer.

## Installation

To install CrossFit, run:

```bash
pip install crossfit
```

## Prerequisites

Before using CrossFit, ensure you have the following installed:

1. Python 3.7 or higher
2. Java Runtime Environment (JRE) - Required for JaCoCo integration
3. The specific coverage tools you intend to use (e.g., JaCoCo, dotnet-coverage)

## Supported Tools

CrossFit currently supports the following coverage tools:

1. **JaCoCo** - Java-based code coverage tool
2. **dotnet-coverage** - .NET coverage tool
3. **dotnet-reportgenerator** - .NET report generation tool

## Usage

CrossFit provides a unified interface for managing code coverage across different tools. Here's how to use it:

### Basic Usage

```python
from crossfit.tools.jacoco import Jacoco

# Initialize the JaCoCo tool
jacoco = Jacoco(tool_path="/path/to/jacoco")

# Save coverage report
result = jacoco.save_report(
    coverage_files=["coverage.exec"],
    target_dir="/output/directory",
    sourcecode_dir="/source/code"
)
```

### Key Features

- **Unified Interface**: Consistent API across different coverage tools
- **Command Building**: Automatic validation of required flags
- **Coverage Management**: Merge, snapshot, and save coverage data
- **Error Handling**: Comprehensive logging and error reporting
- **Multiple Report Formats**: Support for CSV, HTML, XML, and Cobertura formats

### Example Workflow

```python
from crossfit.tools.jacoco import Jacoco
from crossfit.models.tool_models import ReportFormat

# Initialize JaCoCo tool
jacoco = Jacoco(tool_path="/path/to/jacoco")

# Merge coverage files
merge_result = jacoco.merge_coverage(
    coverage_files=["coverage1.exec", "coverage2.exec"],
    target_dir="/output",
    target_file="merged.exec"
)

# Generate HTML report
report_result = jacoco.save_report(
    coverage_files=["merged.exec"],
    target_dir="/reports",
    sourcecode_dir="/src",
    report_format=ReportFormat.Html
)
```

## Package Structure

The package follows a modular structure:

- `crossfit/tools/jacoco.py`: Implementation of JaCoCo tool wrapper
- `crossfit/tools/dotnet_coverage.py`: Implementation of .NET coverage tool wrapper  
- `crossfit/tools/tool.py`: Base tool class and abstract methods
- `crossfit/models/tool_models.py`: Enum definitions for tool types and report formats
- `crossfit/models/command_models.py`: Command result models and command types
- `crossfit/commands/command.py`: Command building and execution utilities

## Core Components

### Tool Models (`crossfit/models/tool_models.py`)

Defines the core enumerations used throughout the package:

- **ToolType**: Enum representing supported tools
  - `Jacoco`
  - `DotnetCoverage` 
  - `DotnetReportGenerator`

- **ReportFormat**: Enum representing supported report formats
  - `Csv`
  - `Html`
  - `Xml`
  - `Cobertura`

### Command Models (`crossfit/models/command_models.py`)

Provides structured representations of command results:

- **CommandType**: Enum defining command types
  - `SaveReport`
  - `SnapshotCoverage`
  - `MergeCoverage`
  - `ResetCoverage`

- **CommandResult**: Pydantic model for command execution results with fields:
  - `code`: Exit code from command execution
  - `command`: The executed command string
  - `output`: Standard output from command
  - `target`: Target path/file of operation
  - `error`: Error output from command

### Command Builder (`crossfit/commands/command.py`)

Provides utilities for building and executing shell commands:

- **Command**: Class for constructing shell commands with:
  - Execution call (e.g., `java -jar`)
  - Command keywords (e.g., `dump`, `merge`, `report`)
  - Options and arguments
  - Path validation
  - Delimiter handling for option-value pairs

## Tool Implementations

### JaCoCo Tool (`crossfit/tools/jacoco.py`)

Implements the JaCoCo coverage tool with methods:

- `save_report()`: Generate coverage reports in various formats
- `snapshot_coverage()`: Take coverage snapshots
- `merge_coverage()`: Merge multiple coverage files
- `_get_command()`: Build validated JaCoCo commands with required flag checking

### DotNet Coverage Tool (`crossfit/tools/dotnet_coverage.py`)

Implements the .NET coverage tool with methods:

- `save_report()`: Generate reports from coverage files
- `merge_coverage()`: Merge coverage data
- `snapshot_coverage()`: Capture coverage snapshots
- `reset_coverage()`: Reset coverage data

## Advanced Usage

### Working with Multiple Report Formats

```python
from crossfit.tools.jacoco import Jacoco
from crossfit.models.tool_models import ReportFormat

jacoco = Jacoco(tool_path="/path/to/jacoco")

# Generate multiple report formats
result = jacoco.save_report(
    coverage_files=["coverage.exec"],
    target_dir="/reports",
    sourcecode_dir="/src",
    report_formats=[ReportFormat.Html, ReportFormat.Xml, ReportFormat.Cobertura]
)
```

### Custom Command Arguments

```python
from crossfit.tools.jacoco import Jacoco

jacoco = Jacoco(tool_path="/path/to/jacoco")

# Pass custom arguments to commands
result = jacoco.merge_coverage(
  ["coverage1.exec", "coverage2.exec"],
  "/output", "merged.exec",
  *["--format", "xml"]  # Custom arguments
)
```
