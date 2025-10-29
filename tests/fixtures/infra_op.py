from typing import Callable, List

from infra_lib import InfraEnvironment
from infra_lib.cli.runner_cli.infra_op_decorator.infra_op import InfraOp


def infra_op_factory(
	name: str = "default_op",
	description: str = "Auto-generated op",
	handler: Callable[[], None] = None,
	handler_return: str = "done",
	target_envs: List[InfraEnvironment] = [],
	depends_on: List[InfraEnvironment] = [],
) -> InfraOp:
	if not handler:
		handler = lambda: handler_return
		handler.__name__ = name

	return InfraOp(
		name=handler.__name__,
		description=description,
		handler=handler,
		target_envs=target_envs,
		depends_on=depends_on,
	)
