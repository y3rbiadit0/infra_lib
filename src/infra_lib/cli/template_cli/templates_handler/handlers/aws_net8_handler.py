from pathlib import Path

from .....enums import InfraEnvironment
from .base_template_handler import BaseTemplateHandler
from .template_file import TemplateFile
from .util import NETContextPrompter


class AWSNet8TemplateHandler(BaseTemplateHandler):
    def get_infra_context(self, env: str) -> dict:
        return {"env": env, "stack_type": self.stack_type}

    def get_env_context(self, env: InfraEnvironment) -> dict:
        return {
            "aws_access_key_id": "test",
            "aws_secret_access_key": "test",
            "aws_default_region": "us-east-1",
            "aws_endpoint_url": "http://localhost:4566",
            "localstack_secrets_manager_url": "http://localstack:4566"
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
            return [
                TemplateFile(
                    source=self.templates_dir
                    / InfraEnvironment.local
                    / "Dockerfile.debug.j2",
                    target=self.project_root
                    / "infrastructure"
                    / InfraEnvironment.local
                    / "Dockerfile.debug",
                    context_provider=lambda: NETContextPrompter(
                        root_dir=self.project_root, defaults={"dotnet_version": "8.0"}
                    ).build_context() | self.get_env_context(env=infra_environment),
                )
            ]
        return []
