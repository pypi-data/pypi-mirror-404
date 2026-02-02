from enum import Enum


class ToolType(Enum):
    Jacoco = "jacococli.jar"
    DotnetCoverage = "dotnet-coverage"
    DotnetReportGenerator = "reportgenerator"


class ReportFormat(Enum):
    Csv = "Csv"
    Html = "Html"
    Xml = "Xml"
    Cobertura = "Cobertura"
