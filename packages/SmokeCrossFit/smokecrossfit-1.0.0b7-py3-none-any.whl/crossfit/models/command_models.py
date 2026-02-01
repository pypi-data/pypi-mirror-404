from enum import Enum
from typing import Optional

from pydantic import BaseModel


class CommandType(Enum):
    SaveReport = "report"
    SnapshotCoverage = "snapshot"
    MergeCoverage = "merge"
    ResetCoverage = "reset"


class CommandResult(BaseModel):
    code: int
    command: str
    output: Optional[str] = ""
    target: Optional[str] = ""
    error: Optional[str] = ""


    def __add__(self, other):
        self.code &= other.code
        self.command += " && " + other.command
        self.output = "\n".join(filter(lambda val: val is not None, (self.output, other.output)))
        self.target = other.target or self.target
        self.error = "\n".join(filter(lambda val: val is not None, (self.error, other.error)))
        return self

    def add_result(self, other):
        return self + other
