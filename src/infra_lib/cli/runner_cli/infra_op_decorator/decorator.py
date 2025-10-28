from collections.abc import Callable
from typing import Dict


from .infra_op import InfraOp, OpHandler
from ....infra.enums import InfraEnvironment

OP_REGISTRY: Dict[str, InfraOp] = {}


def infra_operation(
	description: str,
	name: str | Callable[[str], str] = None,
	target_envs: list[InfraEnvironment] = None,
	depends_on: list[str] = None,
):
	"""
	Decorator to create and register a InfraOperation object.
	"""

	def decorator(func: OpHandler):
		op_name = _handle_name(name, func)
		infra_op = InfraOp(
			name=op_name,
			description=description,
			handler=func,
			target_envs=target_envs.copy() if target_envs else [],
			depends_on=depends_on.copy() if target_envs else [],
		)

		if op_name in OP_REGISTRY:
			raise ValueError(f"Duplicate operation name detected: {name}")

		OP_REGISTRY[op_name] = infra_op

		return func

	return decorator


def _handle_name(name: str, func: Callable):
	func_name = func.__name__.replace("_", "-")

	if name is None:
		op_name = func_name
	elif callable(name):
		op_name = name(func_name)
	else:
		op_name = name
	return op_name
