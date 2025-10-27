from abc import ABC
from dataclasses import InitVar, dataclass, field
from pathlib import Path
import logging
from typing import Callable, Dict, List

from infra_lib.infra.env_context import EnvironmentContext

from .enums import InfraEnvironment

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


class BaseInfraProvider(ABC):
	def __init__(
		self,
		env_context: EnvironmentContext,
	):
		self.env_context = env_context
