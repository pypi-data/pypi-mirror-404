from logging import Logger
from pathlib import Path

import crossfit.refs
from crossfit.tools import Jacoco, DotnetCoverage
from crossfit.models import ToolType


def create_tool(tool_type: ToolType, tool_path: Path = None, logger: Logger = None, catch: bool = True):
    if tool_type == ToolType.Jacoco:
        return Jacoco(logger, tool_path or crossfit.refs.tools_dir, catch)
    elif tool_type == ToolType.DotnetCoverage:
        return DotnetCoverage(logger, tool_path or crossfit.refs.tools_dir, catch)
    else:
        raise ValueError(f"Unknown tool type: {tool_type}")
