from dataclasses import dataclass
from pathlib import Path
import boto3
import logging

from ..enums import InfraEnvironment
from .creds import CredentialsProvider


logger = logging.getLogger(__name__)


@dataclass
class EventBridgeStackConfig:
	template_name: Path
	name: str


class EventBridgeUtil:
	creds: CredentialsProvider
	environment: InfraEnvironment
	_aws_localstack_dir: Path

	def __init__(
		self,
		creds: CredentialsProvider,
		aws_localstack_dir: Path,
		environment: InfraEnvironment,
	):
		self.creds = creds
		self._aws_localstack_dir: Path = aws_localstack_dir
		self.environment = environment

	def template_file(self, file_name: str) -> Path:
		return Path.joinpath(self._aws_localstack_dir, file_name)

	def create_stack(self, stack: EventBridgeStackConfig):
		if not self.template_file(stack.template_name).exists():
			logger.info(f"No EventBridge template at '{self.template_file}', skipping.")
			return

		with open(self.template_file(stack.template_name), "r") as f:
			template_body = f.read()

		cfn = boto3.client(
			"cloudformation",
			endpoint_url=self.creds.url,
			region_name=self.creds.region,
			aws_access_key_id=self.creds.access_key_id,
			aws_secret_access_key=self.creds.secret_access_key,
		)

		try:
			cfn.create_stack(StackName=stack.name, TemplateBody=template_body)
			logger.info(f"EventBridge rule stack '{stack.name}' created.")
		except cfn.exceptions.AlreadyExistsException:
			logger.info(f"EventBridge rule stack '{stack.name}' already exists.")
