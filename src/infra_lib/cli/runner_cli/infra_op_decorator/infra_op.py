from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, List, Protocol, Union

from infra_lib.infra.enums import InfraEnvironment

from ....infra.env_context import EnvironmentContext


OpHandlerFunc = Callable[[EnvironmentContext], Any]
OpHandlerMethod = Callable[[Any, EnvironmentContext], Any]

OpHandler = Union[OpHandlerFunc, OpHandlerMethod]


@dataclass(frozen=True)
class InfraOp:
	name: str
	description: str
	handler: OpHandler
	target_envs: List[InfraEnvironment] = field(default_factory=lambda: None)
	depends_on: List[str] = field(default_factory=list)
