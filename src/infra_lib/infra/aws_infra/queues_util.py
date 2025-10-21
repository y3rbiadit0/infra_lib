import logging
from dataclasses import dataclass
from typing import Optional, Iterable

from mypy_boto3_lambda import LambdaClient
from mypy_boto3_sqs import SQSClient

from .sts_util import STSUtil
from .boto_client_factory import BotoClientFactory
from .aws_services_enum import AwsService
from .creds import CredentialsProvider
from .lambda_util import AWSLambdaParameters


logger = logging.getLogger(__name__)


@dataclass
class AWSQueueConfig:
	name: str
	visibility_timeout: int
	batch_size: int = 10
	batch_window: Optional[int] = None
	report_batch_item_failures: bool = False


class QueuesUtil:
	creds: CredentialsProvider
	_client_factory: BotoClientFactory

	def __init__(self, creds: CredentialsProvider, client_factory: BotoClientFactory):
		self.creds = creds
		self._client_factory = client_factory
		self._sts_util = STSUtil(
			creds=creds,
			client_factory=client_factory,
		)

	@property
	def _sqs_client(self) -> SQSClient:
		return self._client_factory.resource(AwsService.SQS)

	@property
	def _lambda_client(self) -> LambdaClient:
		return self._client_factory.resource(AwsService.LAMBDA)

	def create_queues(self, queues: Iterable[AWSQueueConfig]):
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

	def attach_lambda(self, lambda_func: AWSLambdaParameters, queue_config: AWSQueueConfig):
		account_id = self._sts_util.get_account_id()
		self._lambda_client.create_event_source_mapping(
			EventSourceArn=f"arn:aws:sqs:{self.creds.region}:{account_id}:{queue_config.name}",
			FunctionName=lambda_func.function_name,
			BatchSize=queue_config.batch_size,
			MaximumBatchingWindowInSeconds=queue_config.batch_window or 0,
			FunctionResponseTypes=(
				["ReportBatchItemFailures"] if queue_config.report_batch_item_failures else []
			),
		)
		logger.info(f"Queue {queue_config.name} linked to Lambda {lambda_func.function_name}")
