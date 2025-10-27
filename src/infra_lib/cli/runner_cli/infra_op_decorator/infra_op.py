from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, List, Protocol, TypeVar, Union

from infra_lib.infra.enums import InfraEnvironment

from ....infra.env_context import EnvironmentContext

EnvironmentContextType = TypeVar("EnvironmentContextType", bound=EnvironmentContext)

OpHandlerFunc = Callable[[EnvironmentContextType], Any]
OpHandlerMethod = Callable[[Any, EnvironmentContextType], Any]


OpHandler = Union[OpHandlerFunc, OpHandlerMethod]


@dataclass(frozen=True)
class InfraOp:
	name: str
	description: str
	handler: OpHandler
	target_envs: List[InfraEnvironment] = field(default_factory=lambda: None)
	depends_on: List[str] = field(default_factory=list)
