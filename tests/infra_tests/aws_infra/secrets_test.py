import json
import pytest
from unittest.mock import MagicMock, patch, mock_open

from infra_lib.infra.aws_infra.secrets_util import SecretsManagerUtil
from infra_lib.infra.aws_infra.boto_client_factory import BotoClientFactory
from .aws_fixtures import fake_creds


@pytest.fixture
def mock_client_factory():
	factory = MagicMock(spec=BotoClientFactory)
	mock_secrets_client = MagicMock()
	factory.client.return_value = mock_secrets_client
	return factory, mock_secrets_client


def mock_secrets_file(secrets_dict):
	"""
	Returns a patch context manager that mocks 'open' with the given secrets dictionary.
	"""
	return patch("builtins.open", mock_open(read_data=json.dumps(secrets_dict)))


@pytest.fixture
def secrets_util(fake_creds, mock_client_factory, tmp_path):
	factory, _ = mock_client_factory
	return SecretsManagerUtil(
		creds=fake_creds,
		client_factory=factory,
		aws_config_dir=tmp_path,
	)


def test_create_secrets_file_missing(secrets_util, tmp_path):
	result = secrets_util.create_secrets("nonexistent.json")

	assert result is None
	assert not secrets_util.secrets_client.create_secret.called


def test_create_secrets_creates_new_secret(secrets_util, mock_client_factory):
	_, mock_secrets_client = mock_client_factory
	mock_secrets_client.create_secret.return_value = {"ARN": "arn:aws:secretsmanager:123"}

	expected_key = "secret1"
	expected_value = {"key": "value"}
	secrets_dict = {expected_key: expected_value}

	with mock_secrets_file(secrets_dict):
		secrets_file_path = secrets_util.config_dir / "secrets.json"
		secrets_file_path.write_text(json.dumps(secrets_dict))

		secrets_util.create_secrets("secrets.json")

	mock_secrets_client.create_secret.assert_called_once_with(
		Name=expected_key, SecretString=json.dumps(secrets_dict[expected_key])
	)


def test_create_secrets_skips_existing_secret(secrets_util, mock_client_factory):
	_, mock_secrets_client = mock_client_factory

	secrets_dict = {"secret1": {"key": "value"}}
	expected_secret_str = json.dumps(secrets_dict["secret1"])

	mock_secrets_client.create_secret.side_effect = (
		mock_secrets_client.exceptions.ResourceExistsException
	)

	with mock_secrets_file(secrets_dict):
		secrets_file_path = secrets_util.config_dir / "secrets.json"
		secrets_file_path.write_text(json.dumps(secrets_dict))

		secrets_util.create_secrets("secrets.json")

	mock_secrets_client.create_secret.assert_called_once_with(
		Name="secret1", SecretString=expected_secret_str
	)
