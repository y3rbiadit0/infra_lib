from typing import List

from .....infra.enums import InfraEnvironment
from .base_template_handler import BaseTemplateHandler
from .util import NETContextPrompter
from ..template_file import (
	VSCodeLaunchConfig,
	TemplateFile,
	dotnet_debug_container_task,
)


class AWSNet8LambdaTemplateHandler(BaseTemplateHandler):
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
		}

	def get_extra_files(self, infra_environment: InfraEnvironment) -> List[TemplateFile]:
		templates_env = NETContextPrompter(
			root_dir=self.project_root.parent, defaults={"dotnet_version": "8.0"}
		).build_context()

		files = [
			TemplateFile(
				source=self.templates_dir / "operations" / "deploy.py.j2",
				target=self.project_root / "operations" / "deploy.py",
				context_provider=lambda: templates_env,
			),
			TemplateFile(
				source=self.templates_dir / "aws_config" / "secrets.json",
				target=self.project_root / "aws_config" / "secrets.json",
			),
			TemplateFile(
				source=self.templates_dir / "aws_config" / "apigateway.json.j2",
				target=self.project_root / "aws_config" / "apigateway.json",
				context_provider=lambda: self.get_env_context(InfraEnvironment.stage),
			),
			TemplateFile(
				source=self.templates_dir / "net" / "Environment.cs.j2",
				target=self.project_root.parent / "Environment.cs",
				context_provider=lambda: {"project_name": templates_env["project_name"]},
			),
			TemplateFile(
				source=self.templates_dir / "net" / "LambdaApp.cs.j2",
				target=self.project_root.parent / "LambdaApp.cs",
				context_provider=lambda: {"project_name": templates_env["project_name"]},
			),
			TemplateFile(
				source=self.templates_dir / "net" / "LocalLambdaProxy.cs.j2",
				target=self.project_root.parent / "LocalLambdaProxy.cs",
				context_provider=lambda: {"project_name": templates_env["project_name"]},
			),
			TemplateFile(
				source=self.templates_dir / "net" / "LocalRunner.cs.j2",
				target=self.project_root.parent / "LocalRunner.cs",
				context_provider=lambda: {"project_name": templates_env["project_name"]},
			),
			TemplateFile(
				source=self.templates_dir / "net" / "SecretsManagerUtil.cs.j2",
				target=self.project_root.parent / "SecretsManagerUtil.cs",
				context_provider=lambda: {"project_name": templates_env["project_name"]},
			),
		]

		if infra_environment == InfraEnvironment.local:
			files.append(
				TemplateFile(
					source=self.templates_dir / "local" / "Dockerfile.debug.j2",
					target=self.project_root / "environments" / "local" / "Dockerfile.debug",
					context_provider=lambda: (
						templates_env | self.get_env_context(env=infra_environment)
					),
				)
			)
		return files

	def vscode_configurations(self) -> List[VSCodeLaunchConfig]:
		return [
			dotnet_debug_container_task(container_name=f"debug-{InfraEnvironment.local}"),
		]
