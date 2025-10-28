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

	compose_name: str = "infra"
	pre_compose_actions: List[Callable[[], None]] = None
	post_compose_actions: List[Callable[[], None]] = None
	_custom_profiles: List[str] = field(init=False, default_factory=list)

	def __post_init__(self, custom_profiles: List[str]):
		self._custom_profiles = custom_profiles

	@property
	def profiles(self) -> List[str]:
		return [self.environment.value, *self._custom_profiles]


class DockerCompose:
	"""A component for developers to use for running Docker Compose"""

	def __init__(self, compose_settings: ComposeSettings, env_context: EnvironmentContext):
		self.settings = compose_settings
		self.env_context = env_context

		if not self.settings.compose_file.exists():
			raise FileNotFoundError(f"Docker Compose file {self.settings.compose_file} not found")

	@property
	def _base_command(self) -> str:
		profiles = " ".join(f"--profile {p}" for p in self.settings.profiles)
		return f"docker compose -p {self.settings.compose_name} -f {self.settings.compose_file} {profiles}"

	def _run_compose_command(self, command: str):
		full_command = f"{self._base_command} {command}"
		run_command(full_command, env_vars=self.env_context.env_vars)

	def down(self, remove_volumes: bool = True):
		logger.info("🛑 Stopping containers...")
		profiles = " ".join(f"--profile {p}" for p in self.settings.profiles)

		run_command(
			cmd=f"docker compose -p {self.settings.compose_name} {profiles} "
			f"-f {self.settings.compose_file} down",
			env_vars=self.env_context.env_vars,
		)

		self._run_compose_command(f"down {'-v' if remove_volumes else ''}")

	def build(self):
		logger.info("🏗️  Building containers...")
		self._run_compose_command("build")

	def up(self, detach: bool = True):
		logger.info("🚀 Starting containers...")
		self._run_compose_command(f"up {'-d' if detach else ''}")
