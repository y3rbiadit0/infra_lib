from infra_lib.infra.aws_infra.boto_client_factory import BotoClientFactory
import pytest
from unittest.mock import MagicMock, patch

from infra_lib.infra.aws_infra.creds import CredentialsProvider

from infra_lib.infra.aws_infra.aws_services_enum import AwsService


@pytest.fixture
def fake_creds():
    return CredentialsProvider(
        access_key_id="AKIA_TEST",
        secret_access_key="SECRET_TEST",
        region="us-east-1",
        url="http://localhost:4566",
    )


@patch("boto3.session.Session")
def test_client_creation_and_caching(mock_session_cls, fake_creds):
    # Arrange
    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_session.client.return_value = mock_client
    mock_session_cls.return_value = mock_session

    factory = BotoClientFactory(fake_creds)

    # Act
    client1 = factory.client(AwsService.LAMBDA)
    client2 = factory.client(AwsService.LAMBDA)

    # Assert
    mock_session.client.assert_called_once_with(
        "lambda", endpoint_url=fake_creds.url
    )
    assert client1 is client2


@patch("boto3.session.Session")
def test_resource_creation_and_caching(mock_session_cls, fake_creds):
    # Arrange
    mock_session = MagicMock()
    mock_resource = MagicMock()
    mock_session.resource.return_value = mock_resource
    mock_session_cls.return_value = mock_session

    factory = BotoClientFactory(fake_creds)

    # Act
    resource1 = factory.resource(AwsService.S3)
    resource2 = factory.resource(AwsService.S3)

    # Assert
    mock_session.resource.assert_called_once_with(
        "s3", endpoint_url=fake_creds.url
    )
    assert resource1 is resource2
