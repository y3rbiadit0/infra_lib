from pathlib import Path

from .....infra.enums import InfraEnvironment
from .base_template_handler import BaseTemplateHandler


class AWSGenericTemplateHandler(BaseTemplateHandler):
	"""
	Minimal AWS template handler using the generic infra_<env>.py template.
	Generates:
	  - infra_<env>.py
	  - .env files
	  - docker-compose.yml
	"""

	def __init__(self, templates_dir: Path, project_root: Path, stack_type: str):
		super().__init__(templates_dir, project_root, stack_type, provider="aws")

	def get_infra_context(self, env: InfraEnvironment) -> dict:
		"""Return context for the infra_<env>.py template"""
		return {
			"env": env,
			"stack_type": self.stack_type,
		}

	def get_env_context(self, env: InfraEnvironment) -> dict:
		"""Return context for the .env file template"""
		return {
			"TARGET_ENV": env,
			"AWS_ACCESS_KEY_ID": "test",
			"AWS_SECRET_ACCESS_KEY": "test",
			"AWS_DEFAULT_REGION": "us-east-1",
		}

	def get_docker_context(self) -> dict:
		return {
			"services": [
				"s3",
				"sqs",
				"events",
				"secretsmanager",
				"cloudformation",
				"apigateway",
				"lambda",
			],
			"localstack_volume_dir": "./volume",
		}

	def vscode_configurations(self):
		return []
