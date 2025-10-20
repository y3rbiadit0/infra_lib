import logging
from pathlib import Path

from mypy_boto3_sts import STSClient


from .boto_client_factory import AwsService, BotoClientFactory
from ...enums import InfraEnvironment
from .creds import CredentialsProvider

logger = logging.getLogger(__name__)


class STSUtil:
	_infrastructure_dir: Path
	creds: CredentialsProvider
	environment: InfraEnvironment
	_client_factory: BotoClientFactory
	config_dir: Path

	def __init__(
		self,
		creds: CredentialsProvider,
		environment: InfraEnvironment,
		infrastructure_dir: Path,
		client_factory: BotoClientFactory,
		config_dir: Path,
	):
		self.creds = creds
		self.environment = environment
		self._infrastructure_dir = infrastructure_dir
		self._client_factory = client_factory
		self.config_dir = config_dir

	@property
	def _sts_client(self) -> STSClient:
		return self._client_factory.client(AwsService.STS)

	def get_user_id(self) -> str:
		"""
		Uses STS to get the current AWS user ID for the provided credentials.
		"""
		response = self._sts_client.get_caller_identity()
		return response["UserId"]

	def get_arn(self) -> str:
		"""
		Returns the ARN associated with the credentials.
		"""
		response = self._sts_client.get_caller_identity()
		return response["Arn"]

	def get_account_id(self) -> str:
		"""
		Returns the AWS account ID for the credentials.
		"""
		response = self._sts_client.get_caller_identity()
		return response["Account"]
