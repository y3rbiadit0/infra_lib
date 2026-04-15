from typing import List

from .....infra.enums import InfraEnvironment
from .base_template_handler import BaseTemplateHandler
from ..template_file import TemplateFile, VSCodeLaunchConfig


class AWSLambdaPythonTemplateHandler(BaseTemplateHandler):
	def get_infra_context(self, env: str) -> dict:
		return {"env": env, "stack_type": self.stack_type}

	def get_env_context(self, env: InfraEnvironment) -> dict:
		return {
			"aws_access_key_id": "test",
			"aws_secret_access_key": "test",
			"aws_default_region": "us-east-1",
			"aws_endpoint_url": "http://localstack:4566",
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
			"project_name": self.stack_type,
		}

	def get_extra_files(self, infra_environment: InfraEnvironment) -> List[TemplateFile]:
		project_name = "hello-lambda"
		files = [
			TemplateFile(
				source=self.templates_dir / "operations" / "deploy.py.j2",
				target=self.project_root / "operations" / "deploy.py",
				context_provider=lambda: {"project_name": project_name},
			),
			TemplateFile(
				source=self.templates_dir / "src" / "hello.py",
				target=self.project_root.parent / "src" / f"{project_name}" / "app.py",
			),
			TemplateFile(
				source=self.templates_dir / "src" / "requirements.txt",
				target=self.project_root.parent / "src" / f"{project_name}" / "requirements.txt",
			),
			TemplateFile(
				source=self.templates_dir / "aws_config" / "secrets.json",
				target=self.project_root / "aws_config" / "secrets.json",
			),
			TemplateFile(
				source=self.templates_dir / "aws_config" / "apigateway.json.j2",
				target=self.project_root / "aws_config" / "apigateway.json",
				context_provider=lambda: {
					"project_name": project_name,
					"aws_default_region": self.get_env_context(InfraEnvironment.local)[
						"aws_default_region"
					],
				},
			),
		]
		return files

	def vscode_configurations(self) -> List[VSCodeLaunchConfig]:
		return []
