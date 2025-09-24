import logging
from botocore.exceptions import ClientError
from mypy_boto3_s3 import S3ServiceResource

from .boto_client_factory import BotoClientFactory
from .aws_services_enum import AwsService
from .creds import CredentialsProvider

logger = logging.getLogger(__name__)


class S3Util:
	"""Utility class for AWS S3 operations like bucket creation and file upload."""

	def __init__(self, creds: CredentialsProvider, client_factory: BotoClientFactory):
		self.creds = creds
		self._client_factory = client_factory
		self.__s3_resource: S3ServiceResource | None = None

	@property
	def _s3_resource(self) -> S3ServiceResource:
		"""Get or create the S3 resource."""
		if self.__s3_resource is None:
			self.__s3_resource = self._client_factory.resource(AwsService.S3)
		return self.__s3_resource

	def create_bucket(self, bucket_name: str) -> None:
		"""Create an S3 bucket if it does not exist."""
		bucket = self._s3_resource.Bucket(bucket_name)

		try:
			self._s3_resource.meta.client.head_bucket(Bucket=bucket.name)
			logger.info(f"Bucket '{bucket_name}' already exists.")
			return
		except ClientError as e:
			error_code = int(e.response["Error"]["Code"])
			if error_code != 404:
				logger.error(f"Error checking bucket existence: {e}")
				raise

		try:
			create_bucket_config = {"LocationConstraint": self.creds.region}
			self._s3_resource.create_bucket(
				Bucket=bucket_name, CreateBucketConfiguration=create_bucket_config or None
			)
			logger.info(f"Bucket '{bucket_name}' created.")
		except ClientError as e:
			logger.error(f"Failed to create bucket '{bucket_name}': {e}")
			raise

	def upload_file(self, bucket_name: str, file_path: str, key: str) -> None:
		"""Upload a file to a bucket."""
		try:
			bucket = self._s3_resource.Bucket(bucket_name)
			bucket.upload_file(Filename=file_path, Key=key)
			logger.info(f"File '{file_path}' uploaded to '{bucket_name}/{key}'.")
		except ClientError as e:
			logger.error(f"Failed to upload file '{file_path}' to '{bucket_name}/{key}': {e}")
			raise
