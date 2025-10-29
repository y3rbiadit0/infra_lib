import pytest
import textwrap
import sys
from pathlib import Path
from types import ModuleType

from infra_lib import InfraEnvironment, EnvironmentContext
from infra_lib.cli.runner_cli.context_loader import (
	_import_module_from_path,
	load_env_context_from_arg,
	discover_ops,
)
from infra_lib.cli.runner_cli.exceptions import ConfigError


class TestImportModuleFromPath:
	def test_should_import_valid_module_successfully(self, tmp_path):
		module_file = tmp_path / "test_module.py"
		module_file.write_text("TEST_VAR = 42")
		module_name = "test_module"

		module = _import_module_from_path(module_name, module_file)

		assert isinstance(module, ModuleType)
		assert hasattr(module, "TEST_VAR")
		assert module.TEST_VAR == 42
		assert module_name in sys.modules

	def test_should_raise_config_error_when_file_not_found(self):
		non_existent_path = Path("/nonexistent/path/module.py")

		with pytest.raises(ConfigError, match="Failed to import module"):
			_import_module_from_path("test_module", non_existent_path)

	def test_should_raise_config_error_on_syntax_error(self, tmp_path):
		module_file = tmp_path / "invalid.py"
		module_file.write_text("this is not valid python !!!")

		with pytest.raises(ConfigError, match="Failed to import module"):
			_import_module_from_path("invalid_module", module_file)


class TestLoadEnvContextFromArg:
	def test_should_load_environment_context_successfully(self, tmp_path):
		env = InfraEnvironment.local
		project_root = tmp_path / "infra"
		env_dir = project_root / "environments" / env.value
		env_dir.mkdir(parents=True)

		env_file = env_dir / f"{env.value}.py"
		env_file.write_text(
			textwrap.dedent("""
			from infra_lib import EnvironmentContext, InfraEnvironment

			class LocalContext(EnvironmentContext):
				def load(self):
					pass
				
				def env(self):
					return InfraEnvironment.local
        """)
		)

		context = load_env_context_from_arg(env, project_root)

		assert isinstance(context, EnvironmentContext)
		assert context.env() == env.local

	def test_should_raise_config_error_when_env_file_missing(self, tmp_path):
		env = InfraEnvironment.local
		project_root = tmp_path / "infra"

		with pytest.raises(ConfigError, match="Config file not found"):
			load_env_context_from_arg(env, project_root)

	def test_should_raise_config_error_when_no_context_class_found(self, tmp_path):
		env = InfraEnvironment.local

		project_root = Path(tmp_path / "infra")
		env_dir = Path(project_root / "environments" / env.value)
		env_dir.mkdir(parents=True)

		env_file = Path(env_dir / f"{env.value}.py")
		env_file.write_text("# No EnvironmentContext subclass")

		with pytest.raises(
			ConfigError, match="must define a class that inherits from EnvironmentContext"
		):
			load_env_context_from_arg(env, project_root)

	def test_should_raise_config_error_when_context_instantiation_fails(self, tmp_path):
		env = InfraEnvironment.local
		project_root = Path(tmp_path / "infra")
		env_dir = Path(project_root / "environments" / env.value)
		env_dir.mkdir(parents=True)

		env_file = env_dir / f"{env.value}.py"
		env_file.write_text(
			textwrap.dedent("""
            from infra_lib import EnvironmentContext

            class LocalContext(EnvironmentContext):
                def __init__(self, project_root, environment_dir):
                    super().__init__(project_root, environment_dir)
                    raise ValueError("Initialization failed")
                
                def load(self):
                    pass
            """)
		)

		with pytest.raises(
			ConfigError, match="must define a class that inherits from EnvironmentContext"
		):
			load_env_context_from_arg(env, project_root)


class TestDiscoverOps:
	def test_should_discover_and_import_operation_files(self, tmp_path):
		ops_dir = Path(tmp_path / "operations")
		ops_dir.mkdir()

		op_file = Path(ops_dir / "test_op.py")
		op_file.write_text("OPERATION_NAME = 'test_operation'")

		discover_ops(ops_dir)

		assert "infra.operations.test_op" in sys.modules
		module = sys.modules["infra.operations.test_op"]
		assert hasattr(module, "OPERATION_NAME")
		assert module.OPERATION_NAME == "test_operation"

	def test_should_skip_files_starting_with_underscore(self, tmp_path):
		ops_dir = Path(tmp_path / "operations")
		ops_dir.mkdir()

		private_file = ops_dir / "_private.py"
		private_file.write_text("PRIVATE_VAR = 'should_not_load'")

		discover_ops(ops_dir)

		assert "infra.operations._private" not in sys.modules

	def test_should_discover_nested_operation_files(self, tmp_path):
		ops_dir = Path(tmp_path / "operations")
		nested_dir = Path(ops_dir / "nested" / "deep")
		nested_dir.mkdir(parents=True)

		nested_op = nested_dir / "nested_op.py"
		nested_op.write_text("NESTED_OP = 'deep_operation'")

		discover_ops(ops_dir)

		assert "infra.operations.nested.deep.nested_op" in sys.modules

	def test_should_handle_nonexistent_ops_directory(self, tmp_path, caplog):
		ops_dir = tmp_path / "nonexistent"

		with caplog.at_level("WARNING"):
			discover_ops(ops_dir)

		assert "Operations directory not found" in caplog.text

	def test_should_log_error_for_invalid_operation_file(self, tmp_path, caplog):
		ops_dir = Path(tmp_path / "operations")
		ops_dir.mkdir()

		bad_file = ops_dir / "bad_op.py"
		bad_file.write_text("this is invalid syntax")

		with caplog.at_level("ERROR"):
			discover_ops(ops_dir)

		assert "Could not load operation file" in caplog.text
