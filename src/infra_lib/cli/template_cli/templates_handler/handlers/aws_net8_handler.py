from pathlib import Path
from typing import List


from .....enums import InfraEnvironment
from .base_template_handler import BaseTemplateHandler
from .util import NETContextPrompter
from ..template_file import VSCodeLaunchConfig, TemplateFile, dotnet_local_task


class AWSNet8TemplateHandler(BaseTemplateHandler):
    def get_infra_context(self, env: str) -> dict:
        return {"env": env, "stack_type": self.stack_type}

    def get_env_context(self, env: InfraEnvironment) -> dict:
        return {
            "aws_access_key_id": "test",
            "aws_secret_access_key": "test",
            "aws_default_region": "us-east-1",
            "aws_endpoint_url": "http://localhost:4566",
            "localstack_secrets_manager_url": "http://localstack:4566",
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

    def get_extra_files(self, infra_environment: InfraEnvironment):
        if infra_environment == InfraEnvironment.local:
            templates_env = NETContextPrompter(
                root_dir=self.project_root, defaults={"dotnet_version": "8.0"}
            ).build_context()

            return [
                TemplateFile(
                    source=self.templates_dir
                    / InfraEnvironment.local
                    / "Dockerfile.debug.j2",
                    target=self.project_root
                    / "infrastructure"
                    / InfraEnvironment.local
                    / "Dockerfile.debug",
                    context_provider=lambda: templates_env
                    | self.get_env_context(env=infra_environment),
                ),
                TemplateFile(
                    source=self.templates_dir / "net" / "Environment.cs.j2",
                    target=self.project_root / "Environment.cs",
                    context_provider=lambda: {
                        "project_name": templates_env["project_name"]
                    },
                ),
                TemplateFile(
                    source=self.templates_dir / "aws_config" / "secrets.json",
                    target=self.project_root
                    / "infrastructure"
                    / "aws_config"
                    / "secrets.json",
                    context_provider={},
                ),
            ]

        return []

    def vscode_configurations(self) -> List[VSCodeLaunchConfig]:
        return [
            dotnet_local_task(container_name=f"debug-{InfraEnvironment.local}")
        ]
