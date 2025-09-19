from pathlib import Path

from .....enums import InfraEnvironment
from .base_template_handler import BaseTemplateHandler
from .template_file import TemplateFile
from .util import context_prompter


class AWSNet8TemplateHandler(BaseTemplateHandler):
    def get_infra_context(self, env: str) -> dict:
        return {"env": env, "stack_type": self.stack_type}

    def get_env_context(self, env: str) -> dict:
        return {
            "TARGET_ENV": env,
            "AWS_ACCESS_KEY_ID": "test",
            "AWS_SECRET_ACCESS_KEY": "test",
            "AWS_DEFAULT_REGION": "us-east-1",
        }

    def get_docker_context(self) -> dict:
        return {
            "services": ["s3", "sqs", "events", "secretsmanager", "cloudformation", "apigateway", "lambda"],
            "localstack_volume_dir": "./volume",
        }

    def get_extra_files(self, env: str):
        return [
            TemplateFile(
                source=self.templates_dir / InfraEnvironment.local / "Dockerfile.debug.j2",
                target=self.project_root / "infrastructure" / InfraEnvironment.local / "Dockerfile.debug",
                context_provider=lambda: context_prompter(self.templates_dir / InfraEnvironment.local / "Dockerfile.debug.j2"),
            )
        ]
