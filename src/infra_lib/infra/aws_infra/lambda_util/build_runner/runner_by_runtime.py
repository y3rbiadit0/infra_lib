from mypy_boto3_lambda.literals import RuntimeType

from .base_runner import BuildRunner
from .dotnet_runner import DotnetBuildRunner
from .python_runner import PythonBuildRunner

RUNTIME_BUILDERS: dict[RuntimeType, type[BuildRunner]] = {
    "dotnet8": DotnetBuildRunner,
    "python3.10": PythonBuildRunner,
    "python3.11": PythonBuildRunner,
    "python3.12": PythonBuildRunner,
    "python3.13": PythonBuildRunner,
    "python3.6": PythonBuildRunner,
    "python3.7": PythonBuildRunner,
    "python3.8": PythonBuildRunner,
    "python3.9": PythonBuildRunner,
}
