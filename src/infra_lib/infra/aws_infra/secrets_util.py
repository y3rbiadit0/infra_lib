import json
import os
from pathlib import Path
from typing import Dict
import logging

from mypy_boto3_secretsmanager import SecretsManagerClient

from .boto_client_factory import BotoClientFactory
from .aws_services_enum import AwsService
from .creds import CredentialsProvider

logger = logging.getLogger(__name__)


class SecretsManagerUtil:
	creds: CredentialsProvider
	_client_factory: BotoClientFactory
	config_dir: Path

	def __init__(
		self,
		creds: CredentialsProvider,
		client_factory: BotoClientFactory,
		config_dir: Path,
	):
		self.creds = creds
		self._client_factory = client_factory
		self.config_dir = config_dir

	@property
	def secrets_client(self) -> SecretsManagerClient:
		return self._client_factory.client(AwsService.SECRETS_MANAGER)

	def create_secrets(self, secrets_file: str = "secrets.json"):
		secrets_file_path = Path.joinpath(self.config_dir, secrets_file)
		if not os.path.exists(secrets_file_path):
			logger.info(
				f"No secrets file found at '{secrets_file_path}', skipping secrets creation."
			)
			return

		with open(secrets_file_path, "r") as f:
			secrets: Dict = json.load(f)

		for name, value in secrets.items():
			try:
				value = self.secrets_client.create_secret(Name=name, SecretString=json.dumps(value))
				logger.info(f"Secret '{name}' created.")
			except self.secrets_client.exceptions.ResourceExistsException:
				logger.info(f"Secret '{name}' already exists.")
