import infra_lib
import pytest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Any

from infra_lib.infra.aws_infra.lambda_util.lambda_util import LambdaUtil
from infra_lib.infra.aws_infra.lambda_util.arch_enum import AWSLambdaArchitecture
from infra_lib.infra.aws_infra.lambda_util.lambda_zip_builder import BaseLambdaZipBuilder
from infra_lib.infra.aws_infra.creds import CredentialsProvider
from infra_lib.infra.enums import InfraEnvironment
from infra_lib.infra.aws_infra.boto_client_factory import BotoClientFactory, AwsService
from infra_lib.infra.aws_infra.lambda_util.lambda_util import AWSLambdaParameters
from ..aws_fixtures import fake_creds


class MockLambdaClient:
	"""Mock spec for the LambdaClient."""

	def create_function(self, **kwargs):
		pass

	def update_function_code(self, **kwargs):
		pass

	def add_permission(self, **kwargs):
		pass

	def get_waiter(self, waiter_name: str):
		pass

	@property
	def exceptions(self):
		return MockLambdaExceptions()


class MockLambdaExceptions:
	ResourceConflictException = type("ResourceConflictException", (Exception,), {})
	ResourceNotFoundException = type("ResourceNotFoundException", (Exception,), {})


class MockSTSUtil:
	"""Mock spec for STSUtil."""

	def get_account_id(self) -> str:
		return "123456789012"


class MockAPIGatewayUtil:
	"""Mock spec for APIGatewayUtil."""

	def gateway_config_file(self) -> Dict:
		return {}

	def build_url(self, api_id: str, resource_path: str) -> str:
		return ""


@pytest.fixture
def mock_client_factory() -> tuple[MagicMock, MagicMock]:
	"""
	Provides a mock BotoClientFactory and the mock LambdaClient
	it is configured to return.
	"""
	factory = MagicMock(spec=BotoClientFactory)
	mock_lambda_client = MagicMock(spec=MockLambdaClient)

	# Configure the mock client's exceptions
	mock_lambda_client.exceptions = MockLambdaExceptions()

	factory.client.return_value = mock_lambda_client
	return factory, mock_lambda_client


@pytest.fixture
def mock_sts_util_class() -> MagicMock:
	"""
	Patches the STSUtil class at the module level where LambdaUtil
	imports it. Returns the mock *instance*.
	"""
	with patch(
		"infra_lib.infra.aws_infra.lambda_util.lambda_util.STSUtil", spec=MockSTSUtil
	) as mock_sts_util:
		mock_instance = mock_sts_util.return_value
		mock_instance.get_account_id.return_value = "123456789012"
		yield mock_instance


@pytest.fixture
def mock_apigw_util_class() -> MagicMock:
	with patch(
		"infra_lib.infra.aws_infra.lambda_util.lambda_util.APIGatewayUtil", spec=MockAPIGatewayUtil
	) as MockAPIGWUtil:
		mock_instance = MockAPIGWUtil.return_value
		yield mock_instance


@pytest.fixture
def mock_lambda_builder() -> MagicMock:
	mock_builder = MagicMock(spec=BaseLambdaZipBuilder)
	mock_builder.build.return_value = Path("/fake/output/lambda.zip")
	return mock_builder


@pytest.fixture
def mock_lambda_params(tmp_path: Path) -> MagicMock:
	params = MagicMock(spec=AWSLambdaParameters)
	params.function_name = "test-lambda"
	params.memory_size = 256
	params.timeout_secs = 60
	params.project_root = tmp_path / "lambda_project"
	params.handler = "My.Lambda::Handler"
	params.api_id = "test-api-id"
	params.runtime = "python3.9"
	params.arch = AWSLambdaArchitecture.x86_64
	params.filtered_env_vars = {"VAR1": "VALUE1"}
	params.custom_lambda_builder = None
	return params


@pytest.fixture
def lambda_util(
	fake_creds: CredentialsProvider,
	mock_client_factory: tuple[MagicMock, MagicMock],
	mock_sts_util_class: MagicMock,
	tmp_path: Path,
) -> LambdaUtil:
	factory, _ = mock_client_factory

	util = LambdaUtil(
		creds=fake_creds,
		environment=InfraEnvironment.local,
		project_root=tmp_path / "infra",
		client_factory=factory,
		config_dir=tmp_path / "config",
	)
	return util


class TestLambdaUtil:
	@patch("shutil.rmtree")
	@patch("pathlib.Path.mkdir")
	@patch("infra_lib.infra.aws_infra.lambda_util.lambda_util.DEFAULT_BUILDER_BY_RUNTIME")
	def test_should_build_with_default_builder_when_custom_is_none(
		self,
		mock_default_builders,
		mock_mkdir,
		mock_rmtree,
		lambda_util: LambdaUtil,
		mock_lambda_params: MagicMock,
		mock_lambda_builder: MagicMock,
	):
		mock_builder_class = MagicMock(return_value=mock_lambda_builder)
		mock_default_builders.get.return_value = mock_builder_class
		mock_lambda_params.custom_lambda_builder = None
		mock_lambda_params.runtime = "python3.9"

		zip_path = lambda_util._build_lambda(
			lambda_params=mock_lambda_params, output_dir=lambda_util.output_dir
		)

		mock_default_builders.get.assert_called_with("python3.9")
		mock_builder_class.assert_called_once()
		mock_lambda_builder.build.assert_called_once()
		assert zip_path == mock_lambda_builder.build.return_value

	@patch("shutil.rmtree")
	@patch("pathlib.Path.mkdir")
	def test_should_build_with_custom_builder_when_provided(
		self,
		mock_mkdir,
		mock_rmtree,
		lambda_util: LambdaUtil,
		mock_lambda_params: MagicMock,
		mock_lambda_builder: MagicMock,
	):
		mock_lambda_params.custom_lambda_builder = mock_lambda_builder

		zip_path = lambda_util._build_lambda(
			lambda_params=mock_lambda_params, output_dir=lambda_util.output_dir
		)
		mock_lambda_builder.build.assert_called_once_with(
			project_root=mock_lambda_params.project_root.resolve(),
			build_dir=lambda_util.output_dir / "build" / mock_lambda_params.project_root.name,
			output_dir=lambda_util.output_dir,
			arch=mock_lambda_params.arch,
		)
		assert zip_path == mock_lambda_builder.build.return_value

	@patch("shutil.rmtree")
	@patch("pathlib.Path.mkdir")
	@patch("infra_lib.infra.aws_infra.lambda_util.lambda_util.DEFAULT_BUILDER_BY_RUNTIME", {})
	def test_should_raise_error_when_no_default_or_custom_builder_found(
		self, mock_mkdir, mock_rmtree, lambda_util: LambdaUtil, mock_lambda_params: MagicMock
	):
		mock_lambda_params.custom_lambda_builder = None
		mock_lambda_params.runtime = "unknown-runtime"

		with pytest.raises(NotImplementedError):
			lambda_util._build_lambda(
				lambda_params=mock_lambda_params, output_dir=lambda_util.output_dir
			)

	@patch("builtins.open", new_callable=mock_open, read_data=b"test-zip-bytes")
	def test_should_create_lambda_function_with_correct_parameters(
		self, mock_file: MagicMock, lambda_util: LambdaUtil, mock_lambda_params: MagicMock
	):
		mock_lambda_client = lambda_util._lambda_client
		fake_zip_path = "/fake/lambda.zip"
		expected_role_arn = (
			f"arn:aws:iam::{lambda_util._sts_util.get_account_id()}:role/lambda-role"
		)

		lambda_util._create_lambda(
			zip_path=fake_zip_path, role=expected_role_arn, lambda_params=mock_lambda_params
		)

		mock_file.assert_called_once_with(fake_zip_path, "rb")
		mock_lambda_client.create_function.assert_called_once_with(
			FunctionName=mock_lambda_params.function_name,
			Runtime=mock_lambda_params.runtime,
			Role=expected_role_arn,
			Handler=mock_lambda_params.handler,
			Code={"ZipFile": b"test-zip-bytes"},
			Environment={"Variables": mock_lambda_params.filtered_env_vars},
			MemorySize=mock_lambda_params.memory_size,
			Timeout=mock_lambda_params.timeout_secs,
		)

	@patch("builtins.open", new_callable=mock_open, read_data=b"test-zip-bytes")
	def test_should_skip_create_lambda_if_it_already_exists(
		self, mock_file: MagicMock, lambda_util: LambdaUtil, mock_lambda_params: MagicMock
	):
		mock_lambda_client = lambda_util._lambda_client
		mock_lambda_client.create_function.side_effect = (
			mock_lambda_client.exceptions.ResourceConflictException
		)

		lambda_util._create_lambda(
			zip_path="/fake/lambda.zip", role="fake-role", lambda_params=mock_lambda_params
		)

		mock_lambda_client.create_function.assert_called_once()

	@patch("builtins.open", new_callable=mock_open, read_data=b"new-zip-bytes")
	def test_should_update_lambda_code_and_wait_for_completion(
		self, mock_file: MagicMock, lambda_util: LambdaUtil, mock_lambda_params: MagicMock
	):
		mock_lambda_client = lambda_util._lambda_client
		mock_waiter = MagicMock()
		mock_lambda_client.get_waiter.return_value = mock_waiter
		fake_zip_path = "/fake/lambda.zip"

		lambda_util._update_lambda_code(
			zip_path=fake_zip_path, function_name=mock_lambda_params.function_name
		)

		mock_file.assert_called_once_with(fake_zip_path, "rb")
		mock_lambda_client.update_function_code.assert_called_once_with(
			FunctionName=mock_lambda_params.function_name,
			ZipFile=b"new-zip-bytes",
		)
		mock_lambda_client.get_waiter.assert_called_once_with("function_updated")
		mock_waiter.wait.assert_called_once_with(
			FunctionName=mock_lambda_params.function_name,
			WaiterConfig={"Delay": 5, "MaxAttempts": 12},
		)

	def test_should_add_apigateway_permission_correctly(self, lambda_util: LambdaUtil):
		mock_lambda_client = lambda_util._lambda_client
		function_name = "test-function"
		statement_id = "test-statement"
		expected_source_arn = (
			f"arn:aws:execute-api:{lambda_util.creds.region}:000000000000:local/*/*/*"
		)

		lambda_util._add_lambda_permission_for_apigateway(function_name, statement_id)

		mock_lambda_client.add_permission.assert_called_once_with(
			FunctionName=function_name,
			StatementId=statement_id,
			Action="lambda:InvokeFunction",
			Principal="apigateway.amazonaws.com",
			SourceArn=expected_source_arn,
		)

	def test_should_log_api_gateway_path_when_found(
		self, lambda_util: LambdaUtil, mock_apigw_util_class: MagicMock
	):
		lambda_name = "my-test-lambda"
		api_id = "my-api-id"
		resource_path = "/test/path"
		expected_url = f"http://local-test.com{resource_path}"

		mock_apigw_util = mock_apigw_util_class
		mock_apigw_util.gateway_config_file.return_value = {
			"paths": {
				resource_path: {
					"get": {
						"x-amazon-apigateway-integration": {
							"uri": f"arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:123456789012:function:{lambda_name}/invocations"
						}
					}
				}
			}
		}
		mock_apigw_util.build_url.return_value = expected_url

		with patch.object(
			infra_lib.infra.aws_infra.lambda_util.lambda_util.logger, "info"
		) as mock_logger_info:
			lambda_util._log_lambda_paths_from_apigateway(lambda_name, api_id)

		mock_apigw_util.gateway_config_file.assert_called_once()
		mock_apigw_util.build_url.assert_called_once_with(
			api_id=api_id, resource_path=resource_path
		)

		mock_logger_info.assert_any_call(
			f"Lambda '{lambda_name}' is integrated with API path '{resource_path}' "
			f"(GET) -> URL: {expected_url}"
		)
