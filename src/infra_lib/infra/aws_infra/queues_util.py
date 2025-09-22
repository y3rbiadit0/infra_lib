import logging
from dataclasses import dataclass
from typing import Optional, List

from mypy_boto3_lambda import LambdaClient
from mypy_boto3_sqs import SQSClient

from .boto_client_factory import BotoClientFactory
from .aws_services_enum import AwsService
from .creds import CredentialsProvider


logger = logging.getLogger(__name__)


@dataclass
class AWSQueueConfig:
	name: str
	visibility_timeout: int
	lambda_target: str
	batch_size: int = 10
	batch_window: Optional[int] = None
	report_batch_item_failures: bool = False


class QueuesUtil:
	creds: CredentialsProvider
	_client_factory: BotoClientFactory

	def __init__(self, creds: CredentialsProvider, client_factory: BotoClientFactory):
		self.creds = creds
		self._client_factory = client_factory

	@property
	def _sqs_client(self) -> SQSClient:
		return self._client_factory.resource(AwsService.SQS)

	@property
	def _lambda_client(self) -> LambdaClient:
		return self._client_factory.resource(AwsService.LAMBDA)

	def create_queues(self, queues: List[AWSQueueConfig]):
		for q in queues:
			self._sqs_client.create_queue(
				QueueName=q.name,
				Attributes={
					"FifoQueue": "true",
					"ContentBasedDeduplication": "true",
					"VisibilityTimeout": str(q.visibility_timeout),
				},
			)
			logger.info(f"Queue created: {q.name} (Visibility {q.visibility_timeout}s)")

			self._lambda_client.create_event_source_mapping(
				EventSourceArn=f"arn:aws:sqs:{self.creds.region}:000000000000:{q.name}",
				FunctionName=q.lambda_target,
				BatchSize=q.batch_size,
				MaximumBatchingWindowInSeconds=q.batch_window or 0,
				FunctionResponseTypes=(
					["ReportBatchItemFailures"] if q.report_batch_item_failures else []
				),
			)
			logger.info(f"Queue {q.name} linked to Lambda {q.lambda_target}")
