from typing import Dict

from .infra_op import InfraOp, OpHandler

OP_REGISTRY: Dict[str, InfraOp] = {}


def infra_operation(
	name: str, description: str, target_envs: list[str] = None, depends_on: list[str] = None
):
	"""
	Decorator to create and register a InfraOperation object.
	"""

	def decorator(func: OpHandler):
		infra_op = InfraOp(
			name=name,
			description=description,
			handler=func,
			target_envs=target_envs or ["all"],
			depends_on=depends_on or [],
		)

		if name in OP_REGISTRY:
			raise ValueError(f"Duplicate operation name detected: {name}")

		OP_REGISTRY[name] = infra_op

		return func

	return decorator
