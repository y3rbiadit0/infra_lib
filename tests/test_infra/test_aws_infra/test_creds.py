import pytest
from unittest.mock import patch

from infra_lib.exceptions import ConfigError
from infra_lib.infra.aws_infra import CredentialsProvider

localstack_creds_fixture = {
	"AWS_ACCESS_KEY_ID": "test_key",
	"AWS_SECRET_ACCESS_KEY": "test_secret",
	"AWS_ENDPOINT_URL": "http://localstack:4566",
	"AWS_DEFAULT_REGION": "us-east-1",
}


class TestCredentialsProvider:
	@patch.dict("os.environ", localstack_creds_fixture)
	def test_should_load_all_credentials_from_environment(self):
		creds = CredentialsProvider.from_env()
		expected_url = localstack_creds_fixture["AWS_ENDPOINT_URL"].replace(
			"localstack", "localhost"
		)
		assert creds.access_key_id == localstack_creds_fixture["AWS_ACCESS_KEY_ID"]
		assert creds.secret_access_key == localstack_creds_fixture["AWS_SECRET_ACCESS_KEY"]
		assert creds.region == localstack_creds_fixture["AWS_DEFAULT_REGION"]
		assert creds.url == expected_url

	@patch.dict("os.environ", localstack_creds_fixture, clear=True)
	def test_should_replace_localstack_with_localhost_in_url(self):
		creds = CredentialsProvider.from_env()
		assert not creds.url == "http://localstack:4566"
		assert creds.url == "http://localhost:4566"

	@patch.dict(
		"os.environ",
		{**localstack_creds_fixture, "AWS_ENDPOINT_URL": "http://other-host:4566"},
		clear=True,
	)
	def test_should_not_modify_url_if_localstack_is_absent(self):
		creds = CredentialsProvider.from_env()
		assert creds.url == "http://other-host:4566"

	@patch.dict("os.environ", {}, clear=True)  # clear=True ensures a clean slate
	def test_should_raise_config_error_when_required_vars_are_missing(self):
		with pytest.raises(ConfigError, match="Missing required AWS environment variables"):
			CredentialsProvider.from_env()
