from unittest.mock import MagicMock
from infra_lib.infra.aws_infra.boto_client_factory import BotoClientFactory
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


@pytest.fixture
def mock_client_factory():
	factory = MagicMock(spec=BotoClientFactory)
	mock_client = MagicMock()
	factory.client.return_value = mock_client
	return factory, mock_client
