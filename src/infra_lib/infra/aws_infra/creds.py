import os
from dataclasses import dataclass

from ...exceptions import ConfigError


@dataclass
class CredentialsProvider:
	access_key_id: str
	secret_access_key: str
	url: str
	region: str

	@classmethod
	def from_env(cls) -> "CredentialsProvider":
		required_vars = [
			"AWS_ACCESS_KEY_ID",
			"AWS_SECRET_ACCESS_KEY",
			"AWS_ENDPOINT_URL",
			"AWS_DEFAULT_REGION",
		]
		missing_vars = [var for var in required_vars if not os.getenv(var)]

		if missing_vars:
			raise ConfigError(
				"Missing required AWS environment variables: " + ", ".join(missing_vars)
			)

		endpoint_url = os.getenv("AWS_ENDPOINT_URL")

		return cls(
			access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
			secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
			url=endpoint_url.replace("localstack", "localhost"),
			region=os.getenv("AWS_DEFAULT_REGION"),
		)
