import boto3

from .aws_services_enum import AwsService
from .creds import CredentialsProvider


class BotoClientFactory:
	def __init__(self, creds: CredentialsProvider):
		self._session = boto3.session.Session(
			aws_access_key_id=creds.access_key_id,
			aws_secret_access_key=creds.secret_access_key,
			region_name=creds.region,
		)
		self._endpoint_url = creds.url
		self._cache = {}

	def client(self, service: AwsService):
		if service not in self._cache:
			self._cache[service] = self._session.client(
				service.value,
				endpoint_url=self._endpoint_url,
			)
		return self._cache[service]

	def resource(self, service: AwsService):
		if service not in self._cache:
			self._cache[service] = self._session.resource(
				service.value, endpoint_url=self._endpoint_url
			)
		return self._cache[service]
