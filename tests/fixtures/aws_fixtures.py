import pytest
from typing import Dict
from unittest.mock import MagicMock, patch
from pathlib import Path

from infra_lib.infra.aws_infra import (
	CredentialsProvider,
	AWSLambdaArchitecture,
	AWSLambdaParameters,
	BaseLambdaZipBuilder,
	BotoClientFactory,
)


@pytest.fixture
def fake_creds():
	return CredentialsProvider(
		access_key_id="AKIA_TEST",
		secret_access_key="SECRET_TEST",
		region="us-east-1",
		url="http://localhost:4566",
	)


@pytest.fixture
def mock_client_factory():
	factory = MagicMock(spec=BotoClientFactory)
	mock_client = MagicMock()
	factory.client.return_value = mock_client
	return factory, mock_client


@pytest.fixture
def fake_creds() -> CredentialsProvider:
	return CredentialsProvider(
		access_key_id="AKIA_TEST",
		secret_access_key="SECRET_TEST",
		region="us-east-1",
		url="http://localhost:4566",
	)


@pytest.fixture
def mock_lambda_client_factory() -> tuple[MagicMock, MagicMock]:
	factory = MagicMock(spec=BotoClientFactory)
	mock_lambda_client = MagicMock(spec=MockLambdaClient)

	mock_lambda_client.exceptions = MockLambdaExceptions()

	factory.client.return_value = mock_lambda_client
	return factory, mock_lambda_client


@pytest.fixture
def mock_sts_util_class() -> MagicMock:
	with (
		patch(
			"infra_lib.infra.aws_infra.lambda_util.lambda_util.STSUtil", spec=MockSTSUtil
		) as mock1,
		patch(
			"infra_lib.infra.aws_infra.queues_util.STSUtil", spec=MockSTSUtil, create=True
		) as mock2,
	):
		mock_instance = MagicMock(spec=MockSTSUtil)
		mock_instance.get_account_id.return_value = "123456789012"

		mock1.return_value = mock_instance
		mock2.return_value = mock_instance

		yield mock_instance


@pytest.fixture
def mock_apigw_util_class() -> MagicMock:
	with patch(
		"infra_lib.infra.aws_infra.lambda_util.lambda_util.APIGatewayUtil", spec=MockAPIGatewayUtil
	) as mock_apigw_class:
		mock_instance = mock_apigw_class.return_value
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


class MockLambdaClient:
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


class MockSecretsManagerClient:
	def create_secret(self, **kwargs):
		pass

	@property
	def exceptions(self):
		return MockSecretsManagerExceptions()


class MockSecretsManagerExceptions:
	ResourceExistsException = type("ResourceExistsException", (Exception,), {})


class MockSQSClient:
	def create_queue(self, **kwargs):
		pass


class MockSTSUtil:
	def get_account_id(self) -> str:
		return "123456789012"


class MockAPIGatewayUtil:
	def gateway_config_file(self) -> Dict:
		return {}

	def build_url(self, api_id: str, resource_path: str) -> str:
		return ""
