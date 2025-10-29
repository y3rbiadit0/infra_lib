from infra_lib.cli.runner_cli.infra_op_decorator.infra_op import InfraOp
import pytest
from dataclasses import dataclass, field, FrozenInstanceError
from infra_lib import EnvironmentContext, InfraEnvironment

from ....common_asserts.infra_op_asserts import assert_op_equal
from ....fixtures import infra_op_factory


def _dummy_func_handler(ctx: EnvironmentContext = None):
	"""A standalone function to act as a handler."""
	return "function handled"


class DummyOpHandlers:
	def dummy_method_handler(self, ctx: EnvironmentContext = None):
		return "method handled"


class TestInfraOp:
	def test_instantiation_with_all_params(self):
		envs = [InfraEnvironment.prod, InfraEnvironment.stage]
		deps = ["op-a", "op-b"]
		op = infra_op_factory(
			name=_dummy_func_handler.__name__,
			description="A full operation",
			handler=_dummy_func_handler,
			target_envs=envs,
			depends_on=deps,
		)

		assert op.name == _dummy_func_handler.__name__
		assert op.description == "A full operation"
		assert op.handler is _dummy_func_handler
		assert op.target_envs == envs
		assert op.depends_on == deps

	def test_instantiation_with_defaults(self):
		op = InfraOp(
			name="minimal-op", description="A minimal operation", handler=_dummy_func_handler
		)

		assert op.name == "minimal-op"
		assert op.description == "A minimal operation"
		assert op.handler == _dummy_func_handler
		assert op.target_envs is None
		assert op.depends_on == []

	def test_is_frozen(self):
		op = InfraOp(
			name="frozen-op",
			description="Test immutability",
			handler=_dummy_func_handler,
			target_envs=[InfraEnvironment.local],
			depends_on=["dep-x"],
		)

		with pytest.raises(FrozenInstanceError):
			op.name = "new-name"

		with pytest.raises(FrozenInstanceError):
			op.description = "new-desc"

		with pytest.raises(FrozenInstanceError):
			op.handler = lambda: "new-handler"

		with pytest.raises(FrozenInstanceError):
			op.target_envs = []

		with pytest.raises(FrozenInstanceError):
			op.depends_on = []

	def test_handler_types_are_accepted(self):
		op_func = InfraOp(name="func-op", description="d1", handler=_dummy_func_handler)
		assert op_func.handler(None) == "function handled"

		handler_obj = DummyOpHandlers()
		op_method = InfraOp(
			name="method-op", description="d2", handler=handler_obj.dummy_method_handler
		)
		assert op_method.handler(None) == "method handled"
