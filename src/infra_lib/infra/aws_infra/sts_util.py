import logging
from mypy_boto3_sts import STSClient


from .boto_client_factory import AwsService, BotoClientFactory
from .creds import CredentialsProvider

logger = logging.getLogger(__name__)


class STSUtil:
	creds: CredentialsProvider
	_client_factory: BotoClientFactory

	def __init__(
		self,
		creds: CredentialsProvider,
		client_factory: BotoClientFactory,
	):
		self.creds = creds
		self._client_factory = client_factory

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
