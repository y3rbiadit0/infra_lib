from abc import ABC
from dataclasses import InitVar, dataclass, field
from pathlib import Path
import logging
from typing import Callable, Dict, List

from ..enums import InfraEnvironment

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@dataclass
class ComposeSettings:
	environment: InfraEnvironment
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


class BaseInfra(ABC):
	"""Base class for managing project infrastructure across cloud providers.

	This class defines the structure and required methods for provider-specific
	infrastructure builders. It serves as the common entry point for deploying
	infrastructure using cloud-specific utilities.

	Attributes:
	    env_vars (Dict[str, str]): Environment variables used for deployment.
	    environment (Environment): Target deployment environment (e.g., local, stage, prod).
	"""

	env_vars: Dict[str, str]
	environment: InfraEnvironment

	def __init__(
		self,
		infrastructure_dir: Path,
		project_root: Path,
		project_name: str,
		environment: InfraEnvironment,
		env_vars: Dict[str, str],
	):
		"""Initializes the BaseInfra with project paths and environment.

		Args:
		    infrastructure_dir (Path): Path to the infrastructure configuration directory.
		    project_root (Path): Path to the project source directories.
			project_name (str): Project Name in particular execution.
		    environment (Environment): Deployment environment (local, stage, prod, etc.).
		    env_vars (Dict[str, str]): Environment variables used for deployment.
		"""
		self.environment = environment
		self.infrastructure_dir = infrastructure_dir
		self.project_root = project_root
		self.project_name = project_name
		self.env_vars = env_vars

	def compose_settings(self) -> ComposeSettings:
		return ComposeSettings(custom_profiles=[], pre_compose_actions=[], post_compose_actions=[])
