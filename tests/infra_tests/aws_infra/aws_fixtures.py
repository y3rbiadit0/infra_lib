from infra_lib.infra.aws_infra.creds import CredentialsProvider
import pytest


@pytest.fixture
def fake_creds():
	return CredentialsProvider(
		access_key_id="AKIA_TEST",
		secret_access_key="SECRET_TEST",
		region="us-east-1",
		url="http://localhost:4566",
	)
