import pytest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass, field
from typing import List

from infra_lib.infra.aws_infra.queues_util import QueuesUtil, AWSQueueConfig
from infra_lib.infra.aws_infra.creds import CredentialsProvider
from infra_lib.infra.aws_infra.boto_client_factory import BotoClientFactory
from infra_lib.infra.aws_infra.aws_services_enum import AwsService
from .aws_fixtures import fake_creds


@dataclass
class MockLambdaParams:
	function_name: str
	runtime: str = "python3.9"  # Add a default for simplicity


@pytest.fixture
def mock_client_factory() -> tuple[MagicMock, MagicMock, MagicMock]:
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
def mock_sts_util_class(request) -> MagicMock:
	with patch("infra_lib.infra.aws_infra.queues_util.STSUtil") as MockSTSUtil:
		mock_instance = MagicMock()
		MockSTSUtil.return_value = mock_instance
		yield mock_instance


@pytest.fixture
def queues_util(fake_creds, mock_client_factory, mock_sts_util_class) -> QueuesUtil:
	factory, _, _ = mock_client_factory
	util = QueuesUtil(creds=fake_creds, client_factory=factory)
	return util


class TestQueuesUtil:
	def test_should_create_queues_with_correct_fifo_attributes(
		self, queues_util: QueuesUtil, mock_client_factory
	):
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

	def test_should_attach_lambda_with_defaults_and_no_batch_window(
		self, queues_util: QueuesUtil, mock_client_factory, mock_sts_util_class: MagicMock
	):
		_, _, mock_lambda = mock_client_factory

		test_account_id = "123456789012"
		mock_sts_util_class.get_account_id.return_value = test_account_id

		lambda_func = MockLambdaParams(function_name="my-lambda")
		queue_config = AWSQueueConfig(name="queue1.fifo", visibility_timeout=30, batch_size=5)

		assert queue_config.batch_window is None
		assert queue_config.report_batch_item_failures is False

		queues_util.attach_lambda(lambda_func, queue_config)

		expected_arn = (
			f"arn:aws:sqs:{queues_util.creds.region}:{test_account_id}:{queue_config.name}"
		)
		mock_lambda.create_event_source_mapping.assert_called_once_with(
			EventSourceArn=expected_arn,
			FunctionName="my-lambda",
			BatchSize=5,
			MaximumBatchingWindowInSeconds=0,
			FunctionResponseTypes=[],
		)

	def test_should_attach_lambda_with_batch_window_and_failure_reporting(
		self, queues_util: QueuesUtil, mock_client_factory, mock_sts_util_class: MagicMock
	):
		_, _, mock_lambda = mock_client_factory

		test_account_id = "9876543210"
		mock_sts_util_class.get_account_id.return_value = test_account_id

		lambda_func = MockLambdaParams(function_name="my-other-lambda")
		queue_config = AWSQueueConfig(
			name="queue2.fifo",
			visibility_timeout=60,
			batch_size=10,
			batch_window=15,
			report_batch_item_failures=True,
		)

		queues_util.attach_lambda(lambda_func, queue_config)

		expected_arn = (
			f"arn:aws:sqs:{queues_util.creds.region}:{test_account_id}:{queue_config.name}"
		)
		mock_lambda.create_event_source_mapping.assert_called_once_with(
			EventSourceArn=expected_arn,
			FunctionName="my-other-lambda",
			BatchSize=10,
			MaximumBatchingWindowInSeconds=15,
			FunctionResponseTypes=["ReportBatchItemFailures"],
		)
