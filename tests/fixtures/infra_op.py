from unittest.mock import Mock, MagicMock
from typing import Callable, List

from infra_lib.cli.runner_cli.infra_op_decorator.infra_op import InfraOp
from infra_lib.infra.enums import InfraEnvironment


def infra_op_factory(
	name: str = "default_op",
	description: str = "Auto-generated op",
	handler: Callable = None,
	handler_return: str = "done",
	target_envs: List[InfraEnvironment] = None,
	depends_on: List[str] = None,
) -> InfraOp:
	target_envs = target_envs or []
	depends_on = depends_on or []

	if handler is None:
		handler = lambda ctx: handler_return
		handler.__name__ = name

	elif isinstance(handler, (Mock, MagicMock)):
		if not hasattr(handler, "__name__"):
			handler.__name__ = name
		if not hasattr(handler, "__qualname__"):
			handler.__qualname__ = name

	return InfraOp(
		name=handler.__name__,
		description=description,
		handler=handler,
		target_envs=target_envs,
		depends_on=depends_on,
	)
