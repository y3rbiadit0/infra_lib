import pytest
from unittest.mock import MagicMock, patch

from infra_lib.infra.aws_infra import CredentialsProvider, BotoClientFactory, AwsService

from ...fixtures import fake_creds


@pytest.fixture
def mock_boto_session_cls(fake_creds: CredentialsProvider):
	patch_path = f"boto3.session.Session"

	with patch(patch_path) as mock_session_cls:
		mock_session_instance = MagicMock()
		mock_session_cls.return_value = mock_session_instance

		yield mock_session_cls, mock_session_instance


class TestBotoClientFactory:
	def test_should_create_session_on_init(self, fake_creds, mock_boto_session_cls):
		mock_session_cls, mock_session = mock_boto_session_cls

		factory = BotoClientFactory(fake_creds)
		mock_session_cls.assert_called_once_with(
			aws_access_key_id=fake_creds.access_key_id,
			aws_secret_access_key=fake_creds.secret_access_key,
			region_name=fake_creds.region,
		)

	def test_should_create_and_cache_client_on_first_call(self, fake_creds, mock_boto_session_cls):
		mock_session_cls, mock_session = mock_boto_session_cls
		mock_client = MagicMock()
		mock_session.client.return_value = mock_client

		factory = BotoClientFactory(fake_creds)

		client1 = factory.client(AwsService.LAMBDA)
		client2 = factory.client(AwsService.LAMBDA)

		mock_session.client.assert_called_once_with(
			AwsService.LAMBDA.value, endpoint_url=fake_creds.url
		)

		# Assert cached client
		assert client1 is client2
		assert client1 is mock_client

	def test_should_create_and_cache_resource_on_first_call(
		self, fake_creds, mock_boto_session_cls
	):
		mock_session_cls, mock_session = mock_boto_session_cls
		mock_resource = MagicMock()
		mock_session.resource.return_value = mock_resource

		factory = BotoClientFactory(fake_creds)
		resource1 = factory.resource(AwsService.S3)
		resource2 = factory.resource(AwsService.S3)

		mock_session.resource.assert_called_once_with(
			AwsService.S3.value, endpoint_url=fake_creds.url
		)
		assert resource1 is resource2
		assert resource1 is mock_resource

	def test_should_create_different_clients_for_different_services(
		self, fake_creds, mock_boto_session_cls
	):
		mock_session_cls, mock_session = mock_boto_session_cls
		mock_lambda_client = MagicMock()
		mock_s3_client = MagicMock()

		def client_side_effect(service_name_val, endpoint_url=None):
			if service_name_val == AwsService.LAMBDA.value:
				return mock_lambda_client
			if service_name_val == AwsService.S3.value:
				return mock_s3_client
			return MagicMock()

		mock_session.client.side_effect = client_side_effect
		factory = BotoClientFactory(fake_creds)

		client_lambda = factory.client(AwsService.LAMBDA)
		client_lambda_2 = factory.client(AwsService.LAMBDA)
		client_s3 = factory.client(AwsService.S3)

		assert mock_session.client.call_count == 2

		assert client_lambda is mock_lambda_client
		assert client_lambda_2 is client_lambda
		assert client_s3 is mock_s3_client
		assert client_s3 is not client_lambda

	def test_should_services_resources_be_indistinguible(self, fake_creds, mock_boto_session_cls):
		# TODO: Service and resources are using AWSService - We could split to update this behavior
		mock_session_cls, mock_session = mock_boto_session_cls
		mock_s3_client = MagicMock(name="S3Client")
		mock_s3_resource = MagicMock(name="S3Resource")

		mock_session.client.return_value = mock_s3_client
		mock_session.resource.return_value = mock_s3_resource

		factory = BotoClientFactory(fake_creds)

		client_1 = factory.client(AwsService.S3)
		resource_1 = factory.resource(AwsService.S3)

		mock_session.client.assert_called_once_with(
			AwsService.S3.value, endpoint_url=fake_creds.url
		)
		mock_session.resource.assert_not_called()

		assert client_1 is mock_s3_client
		assert resource_1 is mock_s3_client
		assert resource_1 is not mock_s3_resource
