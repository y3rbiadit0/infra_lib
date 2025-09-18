from pathlib import Path
import os
from dotenv import load_dotenv
from typing import Dict, List, Optional
import logging

from ..enums import Environment
from ..utils import run_command
from ..base_infra import BaseInfraBuilder

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class EnvBuilder:
    """Generic utility to manage infrastructure environments.

    Handles Docker Compose orchestration and project-specific infrastructure deployment.
    """

    def __init__(
        self,
        project_name: str,
        environment: Optional[Environment] = None,
        compose_name: Optional[str] = None,
        infra_dir: Optional[Path] = None,
        projects_dir: Optional[Path] = None,
    ):
        """
        Args:
            project_name (str): Name of the project (used for env vars and compose project name).
            environment (Environment, optional): Deployment environment (local, stage, prod).
                Defaults to ENV['DEPLOY_ENV'] or local.
            compose_name (str, optional): Docker Compose project name. Defaults to project_name.
            infra_dir (Path, optional): Path to infrastructure config directory. Defaults to 'dev'.
            projects_dir (Path, optional): Path to projects directory. Defaults to parent of infra_dir.
        """
        self.project_name = project_name
        self.compose_name = compose_name or project_name

        if environment is None:
            env_value = os.environ.get("TARGET_ENV", Environment.local.value)
            self.environment = Environment(env_value)
        else:
            self.environment = environment

        self.infrastructure_dir = (
            infra_dir or Path(__file__).parent.parent.resolve() / "dev"
        )
        self.projects_dir = projects_dir or self.infrastructure_dir.parent.resolve()
        self.env_vars = self._load_env()

    @property
    def _compose_file(self) -> Path:
        """Path to the Docker Compose YAML file."""
        return self.infrastructure_dir / "docker-compose.yml"

    def _load_env(self) -> Dict:
        """Load environment variables from .env and inject project/environment info."""
        dotenv_path = self.infrastructure_dir / ".env"
        load_dotenv(dotenv_path)
        env = os.environ.copy()
        env["PROJECT_NAME"] = self.project_name
        env["TARGET_ENV"] = self.environment.value
        return env

    def _run_docker_compose(self):
        """Stop, build, and start Docker Compose containers."""
        logger.info("🛑 Stopping containers and removing volumes...")
        run_command(
            f"docker-compose -p {self.compose_name} down -v", env_vars=self.env_vars
        )

        logger.info("🚀 Building containers...")
        run_command(
            f"docker-compose -p {self.compose_name} --profile {self.environment.value} "
            f"-f {self._compose_file} build",
            env_vars=self.env_vars,
        )

        logger.info("🚀 Starting containers...")
        run_command(
            f"docker-compose -p {self.compose_name} --profile {self.environment.value} "
            f"-f {self._compose_file} up -d",
            env_vars=self.env_vars,
        )

    def _build_infra(self, infra_builders: Optional[List[BaseInfraBuilder]] = None):
        """Run project-specific infrastructure builders.

        Args:
            infra_builders (Optional[List[BaseInfraBuilder]]):
                List of BaseInfraBuilder instances (or subclasses) to run.
                If None, defaults to running TpnInfra.
        """
        for builder in infra_builders:
            if not isinstance(builder, BaseInfraBuilder):
                raise TypeError(f"Expected BaseInfraBuilder, got {type(builder)}")
            logger.info(f"🏗 Running builder: {builder.__class__.__name__}")
            builder.build()

    def execute(self, infra_builders: Optional[List[BaseInfraBuilder]] = None):
        """Run the full workflow: Docker Compose + infrastructure."""
        logger.info(f"DEVELOPMENT_MODE={self.environment.value}")
        self._run_docker_compose()
        self._build_infra(infra_builders=infra_builders)
