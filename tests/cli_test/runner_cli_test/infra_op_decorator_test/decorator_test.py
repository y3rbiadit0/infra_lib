from infra_lib.infra.enums import InfraEnvironment
from infra_lib.cli.runner_cli.run_cli import InfraOp
from infra_lib.cli.runner_cli.infra_op_decorator.decorator import infra_operation, OP_REGISTRY

import pytest


@pytest.fixture(autouse=True)
def clear_op_registry():
	"""
	A fixture that automatically clears the global OP_REGISTRY
	before and after each test, ensuring test isolation.
	"""
	OP_REGISTRY.clear()
	yield
	OP_REGISTRY.clear()


def _default_name_generator(name: str):
	return name.replace("_", "-")


def assert_op_equal(op1: InfraOp, op2: InfraOp):
	assert isinstance(op1, InfraOp)
	assert isinstance(op2, InfraOp)

	assert op1.name == op2.name
	assert op1.description == op2.description
	assert op1.handler == op2.handler
	assert op1.target_envs == op2.target_envs
	assert op1.depends_on == op2.depends_on


class TestInfraOperationNaming:
	def test_decorator_registration_basic(self):
		expected_output = "executed"
		dummy_func = lambda: expected_output
		dummy_func.__name__ = "my_test_operation"

		expected_op = InfraOp(
			name=_default_name_generator(dummy_func.__name__),
			description="A test op",
			handler=dummy_func,
			target_envs=[],
			depends_on=[],
		)

		decorator = infra_operation(
			description=expected_op.description,
			target_envs=expected_op.target_envs,
			depends_on=expected_op.depends_on,
		)

		decorated_func = decorator(dummy_func)

		assert expected_op.name in OP_REGISTRY
		assert decorated_func() == expected_output
		assert_op_equal(op1=OP_REGISTRY[expected_op.name], op2=expected_op)

	def test_decorator_implicit_naming(self):
		dummy_func = lambda: "done"
		dummy_func.__name__ = "my_callable_name_op"

		expected_op = InfraOp(
			name=_default_name_generator(dummy_func.__name__),
			description="A callable name op",
			handler=dummy_func,
			target_envs=[],
			depends_on=[],
		)

		decorator = infra_operation(description=expected_op.description)
		decorator(dummy_func)

		assert expected_op.name in OP_REGISTRY
		assert "my_callable_name_op" not in OP_REGISTRY
		assert_op_equal(OP_REGISTRY[expected_op.name], expected_op)

	def test_decorator_registration_callable_name(self):
		"""Tests that a callable passed as 'name' is used to generate the name."""
		dummy_func = lambda: "done"
		dummy_func.__name__ = "my_callable_name_op"

		name_generator = lambda func_name: f"ops:{_default_name_generator(func_name)}"

		# 1. Define the complete expected operation
		expected_op = InfraOp(
			name=name_generator(dummy_func.__name__),
			description="A callable name op",
			handler=dummy_func,
			target_envs=[],  # Expects decorator default
			depends_on=[],  # Expects decorator default
		)

		# 2. Define the decorator, passing the name_generator
		decorator = infra_operation(
			name=name_generator,
			description=expected_op.description,
		)

		# 3. Apply the decorator
		decorated_func = decorator(dummy_func)

		# 4. Assert the operation was registered with the generated name
		assert expected_op.name in OP_REGISTRY
		assert_op_equal(OP_REGISTRY[expected_op.name], expected_op)


class TestInfraOperationRegistration:
	def test_decorator_registration_all_params(self):
		dummy_func = lambda: "done"
		dummy_func.__name__ = "my_full_op"

		expected_op = InfraOp(
			name=_default_name_generator(dummy_func.__name__),
			depends_on=["op-one", "op-two"],
			target_envs=[InfraEnvironment.prod, InfraEnvironment.stage],
			description="A full op",
			handler=dummy_func,
		)

		decorator = infra_operation(
			description="A full op",
			target_envs=expected_op.target_envs,
			depends_on=expected_op.depends_on,
		)

		decorated_func = decorator(dummy_func)

		assert "my-full-op" in OP_REGISTRY

		op = OP_REGISTRY["my-full-op"]
		assert_op_equal(op1=op, op2=expected_op)

		assert op.target_envs is not expected_op.target_envs
		assert op.depends_on is not expected_op.depends_on

	def test_decorator_duplicate_name_explicit(self):
		@infra_operation(description="First op", name="duplicate-name")
		def op_one():
			pass

		with pytest.raises(ValueError, match="Duplicate operation name detected: duplicate-name"):

			@infra_operation(description="Second op", name="duplicate-name")
			def op_two():
				pass

		assert len(OP_REGISTRY) == 1
		assert OP_REGISTRY["duplicate-name"].handler == op_one

	def test_decorator_duplicate_name_implicit(self):
		@infra_operation(description="First op")
		def my_shared_name_op():
			pass

		with pytest.raises(ValueError, match="Duplicate operation name detected: None"):

			@infra_operation(description="Second op")
			def my_shared_name_op():
				pass

		assert len(OP_REGISTRY) == 1
		assert "my-shared-name-op" in OP_REGISTRY
		assert OP_REGISTRY["my-shared-name-op"].description == "First op"

	def test_decorator_duplicate_name_mixed(self):
		"""Tests for a duplicate name collision between an implicit and explicit name."""

		@infra_operation(description="First op")
		def op_one():
			pass

		with pytest.raises(ValueError, match="Duplicate operation name detected: op-one"):

			@infra_operation(description="Second op", name="op-one")
			def op_two():
				pass

		assert len(OP_REGISTRY) == 1
		assert OP_REGISTRY["op-one"].handler == op_one
