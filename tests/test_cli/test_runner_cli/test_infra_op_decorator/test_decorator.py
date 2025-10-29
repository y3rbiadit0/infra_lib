import pytest
from infra_lib.infra.enums import InfraEnvironment
from infra_lib.cli.runner_cli.infra_op_decorator.decorator import infra_operation, OP_REGISTRY


from ....common_asserts.infra_op_asserts import assert_op_equal
from ....fixtures import infra_op_factory


@pytest.fixture(autouse=True)
def clear_op_registry():
	OP_REGISTRY.clear()
	yield
	OP_REGISTRY.clear()


def _decorator_name_builder(name: str):
	return name.replace("_", "-")


class TestInfraOperationNaming:
	def test_decorator_registration_basic(self):
		expected_op = infra_op_factory(
			name=_decorator_name_builder("my_test_operation"),
			description="A test op",
			handler_return="executed",
		)

		decorator = infra_operation(
			description=expected_op.description,
			target_envs=expected_op.target_envs,
			depends_on=expected_op.depends_on,
		)

		decorated_func = decorator(expected_op.handler)

		assert expected_op.name in OP_REGISTRY
		assert decorated_func() == "executed"
		assert_op_equal(
			OP_REGISTRY[expected_op.name.replace("_", "-")],
			expected_op,
		)

	def test_decorator_implicit_naming(self):
		expected_op = infra_op_factory(
			name=_decorator_name_builder("my_callable_name_op"),
			description="A callable name op",
		)
		decorator = infra_operation(description=expected_op.description)
		decorator(expected_op.handler)

		assert expected_op.name in OP_REGISTRY
		assert "my_callable_name_op" not in OP_REGISTRY

		assert_op_equal(OP_REGISTRY[expected_op.name], expected_op)

	def test_decorator_registration_callable_name(self):
		expected_name = f"ops:{_decorator_name_builder('my_callable_name')}"
		custom_name_generator = lambda func_name: f"{_decorator_name_builder(func_name)}"

		expected_op = infra_op_factory(
			name=expected_name,
			description="A callable name op",
		)

		decorator = infra_operation(
			name=custom_name_generator,
			description=expected_op.description,
		)
		decorator(expected_op.handler)

		assert expected_name == expected_op.name
		assert expected_op.name in OP_REGISTRY
		assert_op_equal(OP_REGISTRY[expected_op.name], expected_op)


class TestInfraOperationRegistration:
	def test_decorator_registration_all_params(self):
		expected_name = _decorator_name_builder("my_full_op")
		expected_op = infra_op_factory(
			name=expected_name,
			description="A full op",
			handler_return="done",
			target_envs=[InfraEnvironment.prod, InfraEnvironment.stage],
			depends_on=["op-one", "op-two"],
		)

		decorator = infra_operation(
			description=expected_op.description,
			target_envs=expected_op.target_envs,
			depends_on=expected_op.depends_on,
		)

		decorator(expected_op.handler)

		op = OP_REGISTRY[expected_op.name]
		assert_op_equal(op, expected_op)

	def test_decorator_duplicate_name_explicit(self):
		@infra_operation(description="First op", name="duplicate-name")
		def op_one():
			pass

		with pytest.raises(ValueError, match="Duplicate operation name detected: duplicate-name"):

			@infra_operation(description="Second op", name="duplicate-name")
			def op_two():
				pass

		assert len(OP_REGISTRY) == 1
		assert OP_REGISTRY["duplicate-name"].handler is op_one

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
		"""Tests for a duplicate name collision between implicit and explicit naming."""

		@infra_operation(description="First op")
		def op_one():
			pass

		with pytest.raises(ValueError, match="Duplicate operation name detected: op-one"):

			@infra_operation(description="Second op", name="op-one")
			def op_two():
				pass

		assert len(OP_REGISTRY) == 1
		assert OP_REGISTRY["op-one"].handler is op_one
