import pytest
from infra_lib.infra.aws_infra.sts_util import STSUtil

from ...fixtures import fake_creds, mock_client_factory


@pytest.fixture
def sts_util(fake_creds, mock_client_factory):
	factory, _ = mock_client_factory
	return STSUtil(
		creds=fake_creds,
		client_factory=factory,
	)


class TestSTSUtil:
	def test_should_return_user_id_from_caller_identity(self, sts_util, mock_client_factory):
		_, mock_sts_client = mock_client_factory
		expected_user_id = "TEST_USER_ID_123"
		mock_sts_client.get_caller_identity.return_value = {
			"UserId": expected_user_id,
			"Arn": "arn:aws:iam::123456789012:user/test-user",
			"Account": "123456789012",
		}

		user_id = sts_util.get_user_id()

		mock_sts_client.get_caller_identity.assert_called_once()
		assert user_id == expected_user_id

	def test_should_return_arn_from_caller_identity(self, sts_util, mock_client_factory):
		_, mock_sts_client = mock_client_factory
		expected_arn = "arn:aws:iam::123456789012:user/test-user"
		mock_sts_client.get_caller_identity.return_value = {
			"UserId": "TEST_USER",
			"Arn": expected_arn,
			"Account": "123456789012",
		}

		arn = sts_util.get_arn()

		mock_sts_client.get_caller_identity.assert_called_once()
		assert arn == expected_arn

	def test_should_return_account_id_from_caller_identity(self, sts_util, mock_client_factory):
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

	def test_should_call_sts_client_multiple_times(self, sts_util, mock_client_factory):
		_, mock_sts_client = mock_client_factory

		mock_sts_client.get_caller_identity.side_effect = [
			{
				"UserId": "USER_1",
				"Arn": "ARN_1",
				"Account": "ACCT_1",
			},
			{
				"UserId": "USER_2",
				"Arn": "ARN_2",
				"Account": "ACCT_2",
			},
			{
				"UserId": "USER_3",
				"Arn": "ARN_3",
				"Account": "ACCT_3",
			},
		]

		user_id = sts_util.get_user_id()
		arn = sts_util.get_arn()
		account_id = sts_util.get_account_id()

		assert user_id == "USER_1"
		assert arn == "ARN_2"
		assert account_id == "ACCT_3"
		assert mock_sts_client.get_caller_identity.call_count == 3
