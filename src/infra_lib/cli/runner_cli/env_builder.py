import logging
from pathlib import Path
from typing import Callable, Optional

from ...infra.base_infra import ComposeSettings
from ...utils import run_command
from ..base_env_builder import BaseEnvBuilder
from .task import get_tasks_from_class
from ...enums import InfraEnvironment

logger = logging.getLogger(__name__)


class EnvBuilder(BaseEnvBuilder):
    """
    Handles the 'run' command workflow: Docker Compose and local 'setup' task.
    """

    def execute(self):
        """Run the full workflow: Docker Compose + infrastructure."""
        logger.info(f"Executing workflow for environment: {self.environment.value}")

        compose_settings = self.infra_class.compose_settings()

        for action in compose_settings.pre_compose_actions or []:
            action()

        self._run_docker_compose(compose_settings=compose_settings)

        for action in compose_settings.post_compose_actions or []:
            action()

        self._run_local()


    @property
    def _compose_file(self) -> Path:
        """Returns the path to the main docker-compose.yml file."""
        compose_path = self.project_root / "docker-compose.yml"
        if not compose_path.exists():
            raise FileNotFoundError(f"Docker Compose file {compose_path} not found")
        return compose_path

    def _run_docker_compose(self, compose_settings: ComposeSettings):
        """Stop, build, and start Docker Compose containers."""
        logger.info("🛑 Stopping containers and removing volumes...")
        run_command(
            f"docker compose -p {compose_settings.compose_name} down -v", env_vars=self.env_vars
        )

        profiles = " ".join(f"--profile {p}" for p in compose_settings.profiles)
        logger.info("🏗️  Building containers...")
        run_command(
            f"docker compose -p {compose_settings.compose_name} {profiles} "
            f"-f {self._compose_file} build",
            env_vars=self.env_vars,
        )

        logger.info("🚀 Starting containers...")
        run_command(
            f"docker compose -p {compose_settings.compose_name} {profiles} "
            f"-f {self._compose_file} up -d",
            env_vars=self.env_vars,
        )

    def _run_local(self):
        """Runs the conventional 'setup' task for the local environment."""
        
        if self.environment != InfraEnvironment.local and self.environment != InfraEnvironment.stage:
            logger.warning(f"`run` command is only intended for `local`/`stage` Environment")
            return

        entrypoint = self._look_for_entrypoint()
        
        if entrypoint is None:
            logger.info("Skipping setup task execution.")
            return

        entrypoint(self.infra_class)
        logger.info("✅ Local 'setup' task completed.")

    def _look_for_entrypoint(self) -> Optional[Callable[[], None]]:
        """Looks for a 'setup' task in LocalInfra class."""
        logger.info(f"🛠️  Running local 'setup' task...")

        entrypoint_task_name = "setup"
        setup_task_fn = None
        
        tasks = get_tasks_from_class(self.infra_class)
        setup_task_fn = tasks.get(entrypoint_task_name)

        if setup_task_fn is None:
            logger.warning(f"No '@task' named 'setup' found for '{self.infra_class.__class__.__name__}'.")
            return None
        return setup_task_fn