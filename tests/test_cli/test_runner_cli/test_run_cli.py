from infra_lib.cli.runner_cli.infra_op_decorator.decorator import infra_operation
import pytest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch
from click.testing import CliRunner

from infra_lib.cli.runner_cli.run_cli import (
	run_command,
	_execute_op_with_deps,
	_get_or_create_instance,
)
from infra_lib.cli.runner_cli.infra_op_decorator import OP_REGISTRY
from infra_lib.cli.runner_cli.exceptions import ConfigError, OpError, CycleError
from infra_lib import InfraEnvironment, EnvironmentContext

from ...fixtures import infra_op_factory


@pytest.fixture
def runner():
	return CliRunner()


@pytest.fixture
def mock_context():
	context = Mock(spec=EnvironmentContext)
	context.env.return_value = InfraEnvironment.local
	return context


@pytest.fixture(autouse=True)
def clear_op_registry():
	OP_REGISTRY.clear()
	yield
	OP_REGISTRY.clear()


@pytest.fixture
def mock_discover_and_context(mock_context):
	with (
		patch("infra_lib.cli.runner_cli.run_cli.discover_ops") as mock_discover,
		patch("infra_lib.cli.runner_cli.run_cli.load_env_context_from_arg") as mock_load,
	):
		mock_load.return_value = mock_context
		yield mock_discover, mock_load


class TestRunCli:
	def test_should_require_environment_flag(self, runner):
		result = runner.invoke(run_command, [])

		assert result.exit_code != 0
		assert "Missing option" in result.output or "Error" in result.output

	def test_should_list_available_operations_when_none_specified(
		self, runner, mock_discover_and_context, tmp_path
	):
		env = InfraEnvironment.local
		op = infra_op_factory()
		decorator = infra_operation(name=op.name, target_envs=[InfraEnvironment.local])
		decorated_op = decorator(op.handler)

		with runner.isolated_filesystem():
			result = runner.invoke(run_command, ["-e", env.value, "-p", tmp_path])

		assert result.exit_code == 0
		assert "Available operations" in result.output
		assert op.name in result.output

	@patch("infra_lib.cli.runner_cli.run_cli._execute_op_with_deps")
	def test_should_execute_specified_operations(
		self, mock_execute, runner, mock_discover_and_context, tmp_path
	):
		env = InfraEnvironment.local
		op = infra_op_factory()
		decorator = infra_operation(name=op.name, target_envs=[env])
		decorated_op = decorator(op.handler)

		with runner.isolated_filesystem():
			result = runner.invoke(run_command, ["-e", env.value, "-op", op.name, "-p", tmp_path])

		assert result.exit_code == 0
		mock_execute.assert_called_once()

	def test_should_warn_when_no_operations_found(
		self, runner, mock_discover_and_context, caplog, tmp_path
	):
		with runner.isolated_filesystem():
			with caplog.at_level("WARNING"):
				result = runner.invoke(run_command, ["-e", InfraEnvironment.local, "-p", tmp_path])

		assert result.exit_code == 0
		assert "No operations found" in caplog.text


class TestExecuteOpWithDeps:
	def test_should_execute_operation_without_dependencies(self, mock_context):
		env = InfraEnvironment.local
		op = infra_op_factory(handler=MagicMock(), target_envs=[env])
		decorator = infra_operation(name=op.name, target_envs=[env])
		decorated_op = decorator(op.handler)

		completed = set()

		_execute_op_with_deps(op.name, mock_context, completed, set())

		op.handler.assert_called_once_with(mock_context)
		assert op.name in completed

	def test_should_execute_dependencies_before_operation(self, mock_context):
		execution_order = []

		def dep_op(ctx: EnvironmentContext):
			execution_order.append(dep_op.__name__)

		def main_op(ctx: EnvironmentContext):
			execution_order.append(main_op.__name__)

		env = InfraEnvironment.local
		dep_operation = infra_op_factory(handler=dep_op, target_envs=[env])
		decorator = infra_operation(target_envs=[env])
		decorated_dep_op = decorator(dep_op)

		main_operation = infra_op_factory(
			handler=main_op, target_envs=[env], depends_on=[dep_operation.name.replace("_", "-")]
		)
		decorator = infra_operation(
			target_envs=[env], depends_on=[dep_operation.name.replace("_", "-")]
		)
		decorated_main_op = decorator(main_op)

		_execute_op_with_deps("main-op", mock_context, set(), set())

		assert execution_order == ["dep_op", "main_op"]

	def test_should_not_execute_operation_twice(self, mock_context):
		env = InfraEnvironment.local

		op = infra_op_factory(handler=MagicMock(), target_envs=[env])
		decorator = infra_operation(name=op.name, target_envs=[env])
		decorated_op = decorator(op.handler)
		completed = {op.name}

		_execute_op_with_deps(op.name, mock_context, completed, set())

		op.handler.assert_not_called()

	def test_should_raise_cycle_error_on_circular_dependency(self, mock_context):
		env = InfraEnvironment.local

		op1_name = "op1"
		op2_name = "op2"

		op1 = infra_op_factory(name=op1_name, handler=MagicMock(), target_envs=[env])
		decorator = infra_operation(name=op1.name, target_envs=[env], depends_on=[op2_name])
		decorated_op = decorator(op1.handler)

		op2 = infra_op_factory(name=op2_name, handler=MagicMock(), target_envs=[env])
		decorator = infra_operation(name=op2.name, target_envs=[env], depends_on=[op1.name])
		decorated_op = decorator(op2.handler)

		with pytest.raises(CycleError, match="Circular dependency detected"):
			_execute_op_with_deps("op1", mock_context, set(), set())

	def test_should_raise_op_error_when_operation_not_found(self, mock_context):
		with pytest.raises(OpError, match="Action 'nonexistent' not found"):
			_execute_op_with_deps("nonexistent", mock_context, set(), set())

	def test_should_skip_operation_not_targeted_for_environment(self, mock_context, caplog):
		handler = Mock()

		env = InfraEnvironment.stage

		op = infra_op_factory(handler=MagicMock(), target_envs=[env])
		decorator = infra_operation(name=op.name, target_envs=[env])
		decorated_op = decorator(op.handler)

		with caplog.at_level("INFO"):
			_execute_op_with_deps(op.name, mock_context, set(), set())

		assert "Skipping action" in caplog.text
		handler.assert_not_called()

	def test_should_handle_method_operations_on_class(self, mock_context):
		class TestOps:
			executed: bool

			def __init__(self):
				self.executed = False

			def my_operation(self, ctx):
				self.executed = True

		env = InfraEnvironment.local

		test_instance = TestOps()
		op = infra_op_factory(handler=test_instance.my_operation, target_envs=[env])
		decorator = infra_operation(name=op.name, target_envs=[env])
		decorated_op = decorator(op.handler)

		_execute_op_with_deps(op.name, mock_context, set(), set())

		assert test_instance.executed

	def test_should_raise_op_error_on_handler_execution_failure(self, mock_context):
		def failing_handler(ctx):
			raise ValueError("Handler failed")

		env = InfraEnvironment.local
		op = infra_op_factory(handler=failing_handler, target_envs=[env])
		decorator = infra_operation(name=op.name, target_envs=[env])
		decorated_op = decorator(op.handler)

		with pytest.raises(OpError, match="Failed during execution"):
			_execute_op_with_deps(op.name, mock_context, set(), set())


class TestGetOrCreateInstance:
	def test_should_create_instance_of_class(self):
		class TestClass:
			def __init__(self):
				self.value = 42

		instance = _get_or_create_instance(TestClass)

		assert isinstance(instance, TestClass)
		assert instance.value == 42

	def test_should_return_same_instance_on_subsequent_calls(self):
		class TestClass:
			pass

		instance1 = _get_or_create_instance(TestClass)
		instance2 = _get_or_create_instance(TestClass)

		assert instance1 is instance2

	def test_should_raise_op_error_when_instantiation_fails(self):
		class TestClass:
			def __init__(self):
				raise ValueError("Cannot instantiate")

		with pytest.raises(OpError, match="Failed to auto-instantiate"):
			_get_or_create_instance(TestClass)

	def test_should_raise_op_error_for_class_with_required_params(self):
		class TestClass:
			def __init__(self, required_param):
				self.param = required_param

		with pytest.raises(OpError, match="parameterless __init__"):
			_get_or_create_instance(TestClass)
