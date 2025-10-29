from typing import Tuple
import pytest
from unittest.mock import MagicMock, patch
import json
from pathlib import Path

from infra_lib.infra.aws_infra.boto_client_factory import BotoClientFactory
from infra_lib.infra.aws_infra.secrets_util import SecretsManagerUtil
from .aws_fixtures import fake_creds


@pytest.fixture
def mock_client_factory() -> Tuple[MagicMock, MagicMock]:
	"""
	Provides a mock BotoClientFactory and the mock SecretsManagerClient
	it is configured to return.
	"""
	factory = MagicMock(spec=BotoClientFactory)

	mock_secrets_client = MagicMock(spec=MockSecretsManagerClient)
	mock_secrets_client.exceptions = MagicMock()
	mock_secrets_client.exceptions.ResourceExistsException = MockResourceExistsException

	factory.client.return_value = mock_secrets_client
	return factory, mock_secrets_client


@pytest.fixture
def secrets_util(fake_creds, mock_client_factory, tmp_path: Path) -> SecretsManagerUtil:
	factory, _ = mock_client_factory
	return SecretsManagerUtil(
		creds=fake_creds,
		client_factory=factory,
		aws_config_dir=tmp_path,
	)


class TestSecretsManagerUtil:
	@patch("os.path.exists", return_value=False)
	def test_should_skip_creation_when_secrets_file_is_missing(
		self, mock_path_exists, secrets_util: SecretsManagerUtil
	):
		secrets_util.create_secrets("nonexistent.json")

		secrets_util._client_factory.client.assert_not_called()
		mock_path_exists.assert_called_once_with(secrets_util.config_dir / "nonexistent.json")

	@patch("os.path.exists", return_value=True)
	def test_should_create_secret_when_it_does_not_exist(
		self, mock_path_exists, secrets_util: SecretsManagerUtil, tmp_path: Path
	):
		mock_secrets_client = secrets_util.secrets_client
		mock_secrets_client.create_secret.return_value = {"ARN": "arn:aws:secretsmanager:123"}

		expected_key = "secret1"
		expected_value_dict = {"key": "value"}
		secrets_dict = {expected_key: expected_value_dict}
		secrets_file_name = "secrets.json"

		secrets_file_path = tmp_path / secrets_file_name
		secrets_file_path.write_text(json.dumps(secrets_dict))

		secrets_util.create_secrets(secrets_file_name)

		mock_path_exists.assert_called_once_with(secrets_file_path)
		mock_secrets_client.create_secret.assert_called_once_with(
			Name=expected_key, SecretString=json.dumps(expected_value_dict)
		)

	@patch("os.path.exists", return_value=True)
	def test_should_skip_creation_when_secret_already_exists(
		self, mock_path_exists, secrets_util: SecretsManagerUtil, tmp_path: Path
	):
		mock_secrets_client = secrets_util.secrets_client

		mock_secrets_client.create_secret.side_effect = (
			mock_secrets_client.exceptions.ResourceExistsException
		)

		expected_key = "existing_secret"
		expected_value_dict = {"foo": "bar"}
		secrets_dict = {expected_key: expected_value_dict}
		secrets_file_name = "secrets.json"

		secrets_file_path = tmp_path / secrets_file_name
		secrets_file_path.write_text(json.dumps(secrets_dict))

		secrets_util.create_secrets(secrets_file_name)

		mock_path_exists.assert_called_once_with(secrets_file_path)
		mock_secrets_client.create_secret.assert_called_once_with(
			Name=expected_key, SecretString=json.dumps(expected_value_dict)
		)


class MockBotoException(Exception):
	pass


class MockResourceExistsException(MockBotoException):
	pass


class MockSecretsManagerClient:
	exceptions = MagicMock()
	exceptions.ResourceExistsException = MockResourceExistsException
	create_secret = MagicMock()
