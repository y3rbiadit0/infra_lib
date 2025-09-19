from pathlib import Path
import os
import sys
from dotenv import load_dotenv
from typing import Dict, List, Optional
import logging
import importlib.util

from ...enums import Environment
from ...utils import run_command
from ...infra.base_infra import BaseInfraBuilder

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class EnvBuilder:
    """Generic utility to manage infrastructure environments.

    Handles Docker Compose orchestration and project-specific infrastructure deployment.
    Automatically detects environment folders (local, stage, prod) and loads corresponding
    .env and infra scripts.
    """

    def __init__(
        self,
        project_name: str,
        environment: Optional[Environment] = None,
        compose_name: Optional[str] = "infra",
        project_root: Optional[Path] = None,
    ):
        """
        Args:
            project_name (str): Name of the project (used for env vars and compose project name).
            environment (Environment, optional): Deployment environment (local, stage, prod).
                Defaults to ENV['TARGET_ENV'] or local.
            compose_name (str, optional): Docker Compose project name. Defaults to project_name.
            project_root (Path, optional): Root folder containing environment folders.
                Defaults to parent of this file.
        """
        self.project_name = project_name
        self.compose_name = compose_name or project_name
        self.project_root = project_root

        if environment is None:
            env_value = os.environ.get("TARGET_ENV", Environment.local.value)
            self.environment = Environment(env_value)
        else:
            self.environment = environment

        self.env_vars = self._load_env()

    @property
    def environment_dir(self):
        environment_dir = self.project_root / self.environment.value
        if not environment_dir.exists():
            raise FileNotFoundError(f"Environment folder {environment_dir} not found")
        return environment_dir

    @property
    def compose_file(self):
        compose_path = self.project_root / "docker-compose.yml"
        if not compose_path.exists():
            raise FileNotFoundError(f"Docker Compose file {compose_path} not found")
        return compose_path

    def execute(self, infra_builders: Optional[List[BaseInfraBuilder]] = None):
        """Run the full workflow: Docker Compose + infrastructure."""
        logger.info(f"DEVELOPMENT_MODE={self.environment.value}")
        self._run_docker_compose()
        self._build_infra(infra_builders=infra_builders)

    def _load_env(self) -> Dict:
        """Load environment variables from .env file in environment folder."""
        dotenv_path = next(self.environment_dir.glob(".env*"), None)
        if dotenv_path is None:
            raise FileNotFoundError(f"No .env file found in {self.environment_dir}")
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
            f"-f {self.compose_file} build",
            env_vars=self.env_vars,
        )

        logger.info("🚀 Starting containers...")
        run_command(
            f"docker-compose -p {self.compose_name} --profile {self.environment.value} "
            f"-f {self.compose_file} up -d",
            env_vars=self.env_vars,
        )

    def _build_infra(self, infra_builders: Optional[List[BaseInfraBuilder]] = None):
        """Run project-specific infrastructure builders.

        Args:
            infra_builders (Optional[List[BaseInfraBuilder]]):
                List of BaseInfraBuilder instances (or subclasses) to run.
                If None, automatically loads the environment-specific infra script.
        """
        if infra_builders is None:
            infra_builders = [self._load_infra_builder()]

        for builder in infra_builders:
            if not isinstance(builder, BaseInfraBuilder):
                raise TypeError(f"Expected BaseInfraBuilder, got {type(builder)}")
            logger.info(f"🏗 Running builder: {builder.__class__.__name__}")
            builder.build()

    def _load_infra_builder(self) -> BaseInfraBuilder:
        """Dynamically loads the environment-specific infrastructure class.

        This function imports the `infrastructure` package directly from the
        given `project_root` directory, without requiring it to be installed
        as a Python package. By doing this, developers can run the CLI from
        any working directory and still import `infrastructure` locally.

        The function then looks up an environment-specific entry point class
        inside the `infrastructure` package. The class name is derived from
        the current environment, with the convention:

            - Local → LocalInfra
            - Stage → StageInfra
            - Prod  → ProdInfra

        Returns:
            BaseInfraBuilder: The environment-specific infrastructure builder
            class (e.g., `StageInfra`, `ProdInfra`, etc.), initialized with
            the current project configuration.

        Raises:
            AttributeError: If the expected environment class (e.g.
                "StageInfra") is not found inside the `infrastructure` package.
            FileNotFoundError: If the `__init__.py` file cannot be located at
                the expected path.
        """
        module_path = os.path.join(self.project_root, "__init__.py")
        spec = importlib.util.spec_from_file_location("infrastructure", module_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules["infrastructure"] = module
        spec.loader.exec_module(module)
        class_name = f"{self.environment.value.capitalize()}Infra"
        infra_class = getattr(module, class_name)
        return infra_class(
            infrastructure_dir=self.project_root,
            projects_dir=self.project_root,
            environment=self.environment,
            env_vars=self.env_vars,
        )
