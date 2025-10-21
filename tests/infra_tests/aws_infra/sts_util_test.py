import pytest
from unittest.mock import MagicMock

from infra_lib.infra.aws_infra.boto_client_factory import BotoClientFactory
from infra_lib.infra.aws_infra.sts_util import STSUtil
from infra_lib.enums import InfraEnvironment
from .aws_fixtures import fake_creds


@pytest.fixture
def mock_client_factory():
	factory = MagicMock(spec=BotoClientFactory)
	mock_sts_client = MagicMock()
	factory.client.return_value = mock_sts_client
	return factory, mock_sts_client


@pytest.fixture
def sts_util(fake_creds, mock_client_factory, tmp_path):
	factory, _ = mock_client_factory
	return STSUtil(
		creds=fake_creds,
		environment=InfraEnvironment.local,
		infrastructure_dir=tmp_path,
		client_factory=factory,
		config_dir=tmp_path,
	)


def test_get_user_id(sts_util, mock_client_factory):
	_, mock_sts_client = mock_client_factory
	expected_user_id = "TEST_USER"
	mock_sts_client.get_caller_identity.return_value = {
		"UserId": expected_user_id,
		"Arn": "arn:aws:iam::123456789012:user/test-user",
		"Account": "123456789012",
	}

	user_id = sts_util.get_user_id()

	mock_sts_client.get_caller_identity.assert_called_once()
	assert user_id == expected_user_id


def test_get_arn(sts_util, mock_client_factory):
	_, mock_sts_client = mock_client_factory
	expected_arn = "arn:aws:iam::123456789012:user/test-user"
	mock_sts_client.get_caller_identity.return_value = {
		"UserId": "TEST_USER",
		"Arn": "arn:aws:iam::123456789012:user/test-user",
		"Account": "123456789012",
	}

	arn = sts_util.get_arn()

	mock_sts_client.get_caller_identity.assert_called_once()
	assert arn == expected_arn


def test_get_account_id(sts_util, mock_client_factory):
	_, mock_sts_client = mock_client_factory
	expected_account_id = "123456789012"
	mock_sts_client.get_caller_identity.return_value = {
		"UserId": "TEST_USER",
		"Arn": "arn:aws:iam::123456789012:user/test-user",
		"Account": expected_account_id,
	}

	account_id = sts_util.get_account_id()

	mock_sts_client.get_caller_identity.assert_called_once()
	assert account_id == expected_account_id
