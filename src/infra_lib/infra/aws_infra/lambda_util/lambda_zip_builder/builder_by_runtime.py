from mypy_boto3_lambda.literals import RuntimeType

from .base_lambda_zip_builder import BaseLambdaZipBuilder
from .dotnet_lambda_zip_builder import DotnetZipBuilder
from .python_lambda_zip_builder import PythonZipBuilder

DEFAULT_BUILDER_BY_RUNTIME: dict[RuntimeType, type[BaseLambdaZipBuilder]] = {
	"dotnet8": DotnetZipBuilder,
	"python3.10": PythonZipBuilder,
	"python3.11": PythonZipBuilder,
	"python3.12": PythonZipBuilder,
	"python3.13": PythonZipBuilder,
	"python3.6": PythonZipBuilder,
	"python3.7": PythonZipBuilder,
	"python3.8": PythonZipBuilder,
	"python3.9": PythonZipBuilder,
}
