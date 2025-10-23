import pytest
from unittest.mock import MagicMock

from infra_lib.infra.aws_infra.queues_util import QueuesUtil, AWSQueueConfig
from infra_lib.infra.aws_infra.creds import CredentialsProvider
from infra_lib.infra.aws_infra.boto_client_factory import BotoClientFactory, AwsService
from infra_lib.infra.aws_infra.lambda_util import AWSLambdaParameters


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

	mock_sqs = MagicMock()
	mock_lambda = MagicMock()

	def resource_side_effect(service):
		if service == AwsService.SQS:
			return mock_sqs
		if service == AwsService.LAMBDA:
			return mock_lambda
		raise ValueError(f"Unknown service {service}")

	factory.resource.side_effect = resource_side_effect
	return factory, mock_sqs, mock_lambda


@pytest.fixture
def queues_util(fake_creds, mock_client_factory):
	factory, _, _ = mock_client_factory
	return QueuesUtil(creds=fake_creds, client_factory=factory)


def test_create_queues(queues_util, mock_client_factory):
	_, mock_sqs, _ = mock_client_factory

	queue_configs = [
		AWSQueueConfig(name="queue1.fifo", visibility_timeout=30),
		AWSQueueConfig(name="queue2.fifo", visibility_timeout=45, batch_window=5),
	]

	queues_util.create_queues(queue_configs)

	mock_sqs.create_queue.assert_any_call(
		QueueName="queue1.fifo",
		Attributes={
			"FifoQueue": "true",
			"ContentBasedDeduplication": "true",
			"VisibilityTimeout": "30",
		},
	)
	mock_sqs.create_queue.assert_any_call(
		QueueName="queue2.fifo",
		Attributes={
			"FifoQueue": "true",
			"ContentBasedDeduplication": "true",
			"VisibilityTimeout": "45",
		},
	)
	assert mock_sqs.create_queue.call_count == 2


def test_attach_lambda(queues_util, mock_client_factory):
	_, _, mock_lambda = mock_client_factory

	queues_util._sts_util.get_account_id = MagicMock(return_value="123456789012")

	lambda_func = AWSLambdaParameters(function_name="my-lambda", runtime="python3.9")
	queue_config = AWSQueueConfig(name="queue1.fifo", visibility_timeout=30, batch_size=5)

	queues_util.attach_lambda(lambda_func, queue_config)

	mock_lambda.create_event_source_mapping.assert_called_once_with(
		EventSourceArn="arn:aws:sqs:us-east-1:123456789012:queue1.fifo",
		FunctionName="my-lambda",
		BatchSize=5,
		MaximumBatchingWindowInSeconds=0,
		FunctionResponseTypes=[],
	)
