import logging

from mypy_boto3_s3 import S3ServiceResource

from .boto_client_factory import BotoClientFactory
from .aws_services_enum import AwsService
from .creds import CredentialsProvider

logger = logging.getLogger(__name__)


class S3Util:
    creds: CredentialsProvider
    _client_factory: BotoClientFactory

    def __init__(self, creds: CredentialsProvider, client_factory: BotoClientFactory):
        self.creds = creds
        self._client_factory = client_factory

    @property
    def _s3_resource(self) -> S3ServiceResource:
        return self._client_factory.resource(AwsService.S3)

    def create_bucket(self, bucket_name: str):

        bucket = self._s3_resource.Bucket(bucket_name)
        exists = True
        try:
            self._s3_resource.meta.client.head_bucket(Bucket=bucket_name)
        except:
            exists = False

        if not exists:
            self._s3_resource.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={"LocationConstraint": self.creds.region},
            )
            logger.info(f"Bucket '{bucket_name}' created.")
        else:
            logger.info(f"Bucket '{bucket_name}' already exists.")
