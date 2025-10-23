from pathlib import Path
import logging
from typing import Dict


from .boto_client_factory import BotoClientFactory
from .creds import CredentialsProvider
from .eventbridge_util import EventBridgeUtil
from .lambda_util import LambdaUtil
from .queues_util import QueuesUtil
from .sts_util import STSUtil
from .s3_util import S3Util
from .secrets_util import SecretsManagerUtil
from .api_gateway_util import APIGatewayUtil
from ...enums import InfraEnvironment
from ..base_infra import BaseInfra

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class AWSInfraBuilder(BaseInfra):
	"""Builder class to provision and manage AWS infrastructure resources.

	Provides utility methods for interacting with AWS services (S3, Lambda, SQS, EventBridge,
	Secrets Manager, API Gateway) using LocalStack or real AWS environments.

	Attributes:
	    lambda_util (LambdaUtil): Utility for managing Lambda functions.
	    queues_util (QueuesUtil): Utility for managing SQS queues.
	    s3_util (S3Util): Utility for managing S3 buckets.
	    eventbridge_util (EventBridgeUtil): Utility for managing EventBridge rules and events.
	    secrets_util (SecretsManagerUtil): Utility for managing Secrets Manager secrets.
	    api_gateway_util (APIGatewayUtil): Utility for managing API Gateway endpoints.
	    env_vars (Dict[str, str]): Environment variables used for deployment.
	    infrastructure_dir (Path): Path to infrastructure configuration directory.
	    projects_dir (Path): Path to project source directories.
	    config_dir (Path): Directory where AWS configuration JSON files are stored.
	    creds (CredentialsProvider): AWS credentials provider.
	    environment (Environment): Target deployment environment (e.g., local, stage, prod).
	"""

	lambda_util: LambdaUtil
	queues_util: QueuesUtil
	s3_util: S3Util
	eventbridge_util: EventBridgeUtil
	secrets_util: SecretsManagerUtil
	api_gateway_util: APIGatewayUtil
	sts_util: STSUtil
	env_vars: Dict[str, str]

	def __init__(
		self,
		infrastructure_dir: Path,
		project_root: Path,
		project_name: str,
		environment: InfraEnvironment,
		env_vars: Dict[str, str],
		config_dir: str = "aws_config",
	):
		self.infrastructure_dir = infrastructure_dir
		self.project_root = project_root
		self.project_name = project_name
		self.config_dir = Path.joinpath(self.infrastructure_dir, config_dir)

		self.creds = CredentialsProvider.from_env()

		self._client_factory = BotoClientFactory(self.creds)
		self.environment = environment
		self.env_vars = env_vars

		self.secrets_util = SecretsManagerUtil(
			creds=self.creds,
			client_factory=self._client_factory,
			config_dir=self.config_dir,
		)
		self.s3_util = S3Util(creds=self.creds, client_factory=self._client_factory)
		self.queues_util = QueuesUtil(creds=self.creds, client_factory=self._client_factory)
		self.api_gateway_util = APIGatewayUtil(
			creds=self.creds,
			environment=self.environment,
			client_factory=self._client_factory,
			config_dir=self.config_dir,
		)
		self.lambda_util = LambdaUtil(
			creds=self.creds,
			environment=self.environment,
			infrastructure_dir=self.infrastructure_dir,
			client_factory=self._client_factory,
			config_dir=self.config_dir,
		)
		self.eventbridge_util = EventBridgeUtil(
			creds=self.creds,
			aws_localstack_dir=self.config_dir,
			environment=environment,
		)
		self.sts_util = STSUtil(
			creds=self.creds,
			client_factory=self._client_factory,
		)
