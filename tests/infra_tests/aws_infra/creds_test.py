import pytest
from unittest.mock import patch

from infra_lib.infra.aws_infra.creds import CredentialsProvider

localstack_creds_fixture = {
	"AWS_ACCESS_KEY_ID": "test_key",
	"AWS_SECRET_ACCESS_KEY": "test_secret",
	"AWS_ENDPOINT_URL": "http://localstack:4566",
	"AWS_DEFAULT_REGION": "us-east-1",
}


@patch.dict("os.environ", localstack_creds_fixture)
def test_credentials_provider_from_env():
	"""
	Tests that from_env correctly reads from os.environ
	and performs the URL replacement.
	"""
	creds = CredentialsProvider.from_env()

	expected_url = localstack_creds_fixture["AWS_ENDPOINT_URL"].replace("localstack", "localhost")
	assert creds.access_key_id == localstack_creds_fixture["AWS_ACCESS_KEY_ID"]
	assert creds.secret_access_key == localstack_creds_fixture["AWS_SECRET_ACCESS_KEY"]
	assert creds.region == localstack_creds_fixture["AWS_DEFAULT_REGION"]
	assert creds.url == expected_url


@patch.dict("os.environ", {"AWS_ENDPOINT_URL": "http://localstack:4566"})
def test_from_env_replaces_localstack_with_localhost_in_url():
	"""
	Tests that from_env correctly reads from os.environ
	and performs the URL replacement.
	"""
	creds = CredentialsProvider.from_env()
	assert not creds.url == "http://localstack:4566"
	assert creds.url == "http://localstack:4566".replace("localstack", "localhost")

@patch.dict("os.environ", {"AWS_ENDPOINT_URL": "http://localhost:4566"})
def test_from_env_does_not_replace_url_if_no_localstack():
	"""
	Tests that from_env leaves the endpoint URL unchanged
	if it does not contain 'localstack'.
	"""
	creds = CredentialsProvider.from_env()
	assert creds.url == "http://localhost:4566"


@patch.dict("os.environ", {}, clear=True)  # clear=True ensures a clean slate
def test_credentials_provider_from_env_missing_vars():
	"""
	Tests the failure case where environment variables are missing.
	The code will fail on .replace() for a NoneType.
	"""
	with pytest.raises(AttributeError, match="'NoneType' object has no attribute 'replace'"):
		CredentialsProvider.from_env()