import json
from dataclasses import InitVar, dataclass, field
import logging
from typing import Callable, List
from pathlib import Path


from ..infra.env_context import EnvironmentContext
from ..infra.enums import InfraEnvironment
from .command_utils import run_command

logger = logging.getLogger(__name__)


@dataclass
class ComposeSettings:
	environment: InfraEnvironment
	compose_file: Path
	custom_profiles: InitVar[List[str]]
	compose_files: List[Path] | None = None

	compose_name: str = "infra"
	pre_compose_actions: List[Callable[[], None]] = None
	post_compose_actions: List[Callable[[], None]] = None
	_custom_profiles: List[str] = field(init=False, default_factory=list)

	def __post_init__(self, custom_profiles: List[str]):
		self._custom_profiles = custom_profiles

	@property
	def profiles(self) -> List[str]:
		return [self.environment.value, *self._custom_profiles]

	@property
	def resolved_compose_files(self) -> List[Path]:
		return self.compose_files or [self.compose_file]


class DockerCompose:
	"""A component for developers to use for running Docker Compose"""

	def __init__(self, compose_settings: ComposeSettings, env_context: EnvironmentContext):
		self.settings = compose_settings
		self.env_context = env_context

		missing_files = [
			compose_file
			for compose_file in self.settings.resolved_compose_files
			if not compose_file.exists()
		]
		if missing_files:
			raise FileNotFoundError(f"Docker Compose file {missing_files[0]} not found")

	@property
	def _base_command(self) -> str:
		compose_files = " ".join(
			f"-f {compose_file}" for compose_file in self.settings.resolved_compose_files
		)
		profiles = " ".join(f"--profile {p}" for p in self.settings.profiles)
		return f"docker compose -p {self.settings.compose_name} {compose_files} {profiles}"

	def _run_compose_command(self, command: str):
		full_command = f"{self._base_command} {command}"
		run_command(full_command, env_vars=self.env_context.host_env_vars)

	def _write_infra_env_file(self) -> Path:
		"""Write the fully resolved project environment next to the compose file."""
		env_file = self.env_context.project_root / ".infra-generated.env"
		lines = [
			f"{key}={json.dumps(value)}"
			for key, value in self.env_context.container_env_vars.items()
		]
		env_file.write_text("\n".join(lines) + "\n")
		return env_file

	def down(self, remove_volumes: bool = False):
		logger.info("Stopping containers")
		command = "down -v" if remove_volumes else "down"
		self._run_compose_command(command)

	def build(self):
		logger.info("Building containers")
		self._run_compose_command("build")

	def up(self, detach: bool = True):
		logger.info("Starting containers")
		self._write_infra_env_file()
		self._run_compose_command(f"up {'-d' if detach else ''}")
