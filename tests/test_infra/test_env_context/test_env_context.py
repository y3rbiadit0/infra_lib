import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from infra_lib import EnvironmentContext, InfraEnvironment
from ...fixtures import target_env_var_fixture


class ConcreteEnvironmentContext(EnvironmentContext):
	def __init__(self, project_root: Path, environment_dir: Path, env_type: InfraEnvironment):
		super().__init__(project_root, environment_dir)
		self._env_type = env_type

	def env(self) -> InfraEnvironment:
		return self._env_type


class TrackableEnvironmentContext(ConcreteEnvironmentContext):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.pre_load_called = False
		self.pre_load_call_count = 0

	def pre_load_action(self):
		self.pre_load_called = True
		self.pre_load_call_count += 1


@pytest.fixture
def project_root(tmp_path) -> Path:
	return Path(tmp_path / "infra")


@pytest.fixture
def environment_dir(tmp_path) -> Path:
	env_dir = Path(tmp_path / "infra" / "environments")
	env_dir.mkdir(parents=True, exist_ok=True)
	return env_dir


@pytest.fixture
def mock_infra_env() -> InfraEnvironment:
	return InfraEnvironment.local


@pytest.fixture
def context(
	project_root: Path, environment_dir: Path, mock_infra_env
) -> ConcreteEnvironmentContext:
	return ConcreteEnvironmentContext(project_root, environment_dir, mock_infra_env)


@pytest.fixture
def trackable_context(
	project_root: Path, environment_dir: Path, mock_infra_env
) -> TrackableEnvironmentContext:
	return TrackableEnvironmentContext(project_root, environment_dir, mock_infra_env)


@pytest.fixture
def dotenv_path(environment_dir: Path, mock_infra_env: InfraEnvironment):
	path = Path(environment_dir.parent / mock_infra_env.value)
	path.mkdir(parents=True, exist_ok=True)
	return Path(path / ".env")


@pytest.fixture
def populated_dotenv(dotenv_path: Path) -> Path:
	dotenv_path.write_text("VAR1=value1\nVAR2=value2\nVAR3=value3\n")
	return dotenv_path


@pytest.fixture
def mock_environ():
	with patch("os.environ", {}):
		yield


class TestEnvironmentContextInitialization:
	def test_should_set_all_attributes_on_initialization(
		self, project_root, environment_dir, mock_infra_env
	):
		context = ConcreteEnvironmentContext(project_root, environment_dir, mock_infra_env)

		assert context.project_root == project_root
		assert context.environment_dir == environment_dir
		assert context.env_vars == {}
		assert isinstance(context.env_vars, dict)

	def test_should_not_allow_direct_instantiation_of_abstract_class(
		self, project_root, environment_dir
	):
		with pytest.raises(TypeError, match="Can't instantiate abstract class"):
			EnvironmentContext(project_root, environment_dir)

	def test_should_require_env_method_implementation_in_subclasses(
		self, project_root, environment_dir
	):
		class IncompleteContext(EnvironmentContext):
			pass

		with pytest.raises(TypeError):
			IncompleteContext(project_root, environment_dir)

	def test_should_return_correct_environment_value(self, context, mock_infra_env):
		assert context.env() == mock_infra_env


class TestEnvironmentContextPaths:
	def test_should_return_correct_dotenv_path_structure(
		self, context, environment_dir, mock_infra_env
	):
		expected_path = environment_dir.parent / mock_infra_env.value / ".env"
		assert context.get_dotenv_path() == expected_path

	def test_should_generate_different_paths_for_different_environments(
		self, project_root, environment_dir
	):
		envs = [InfraEnvironment.local, InfraEnvironment.stage, InfraEnvironment.prod]

		for env_name in envs:
			mock_env = MagicMock(value=env_name)
			context = ConcreteEnvironmentContext(project_root, environment_dir, mock_env)

			expected_path = environment_dir.parent / env_name / ".env"
			assert context.get_dotenv_path() == expected_path


class TestEnvironmentContextPreLoadAction:
	def test_should_execute_default_pre_load_action_without_errors(self, context):
		try:
			context.pre_load_action()
		except Exception as e:
			pytest.fail(f"pre_load_action raised {e}")

	def test_should_allow_pre_load_action_override_in_subclasses(self, trackable_context):
		trackable_context.pre_load_action()
		assert trackable_context.pre_load_called is True
		assert trackable_context.pre_load_call_count == 1

	def test_should_call_pre_load_action_during_load(self, trackable_context):
		trackable_context.load()
		assert trackable_context.pre_load_called is True


class TestEnvironmentContextLoadBasics:
	def test_should_update_os_environ_during_load(self, context, mock_environ):
		expected_env_vars = {"other_env": "other_value"}
		os.environ.update(expected_env_vars)
		assert target_env_var_fixture() not in os.environ

		context.load()
		assert target_env_var_fixture() in os.environ


class TestEnvironmentContextLoadWithDotenv:
	"""Tests for loading with .env files."""

	def test_should_load_all_variables_from_existing_dotenv(
		self, context, populated_dotenv, mock_environ
	):
		context.load()

		assert context.env_vars.get("VAR1") == "value1"
		assert context.env_vars.get("VAR2") == "value2"
		assert context.env_vars.get("VAR3") == "value3"

	def test_should_handle_empty_dotenv_file_gracefully(
		self, context, dotenv_path, mock_infra_env, mock_environ
	):
		dotenv_path.write_text("")
		context.load()

		assert target_env_var_fixture() in context.env_vars
		assert context.env_vars[target_env_var_fixture()] == mock_infra_env.value

	def test_should_handle_malformed_dotenv_entries(self, context, dotenv_path, mock_environ):
		dotenv_path.write_text(
			"VALID_VAR=valid\nINVALID LINE WITHOUT EQUALS\nANOTHER_VALID=value\n"
		)

		context.load()
		assert "VALID_VAR" in context.env_vars
		assert "ANOTHER_VALID" in context.env_vars

	def test_should_handle_special_characters_in_dotenv_values(
		self, context, dotenv_path, mock_environ
	):
		dotenv_path.write_text(
			"URL=https://example.com/path?query=value&other=123\n"
			"PATH=/usr/local/bin:/usr/bin\n"
			'QUOTED="value with spaces"\n'
		)

		context.load()
		assert "URL" in context.env_vars
		assert "PATH" in context.env_vars


class TestEnvironmentContextLoadWithExtraVars:
	def test_should_merge_extra_vars_with_loaded_config(
		self, context, mock_infra_env, mock_environ
	):
		extra_vars = {"EXTRA1": "extra_value1", "EXTRA2": "extra_value2"}
		context.load(extra_vars=extra_vars)

		assert context.env_vars.get("EXTRA1") == "extra_value1"
		assert context.env_vars.get("EXTRA2") == "extra_value2"
		assert context.env_vars.get(target_env_var_fixture()) == mock_infra_env.value

	def test_should_allow_extra_vars_to_override_dotenv_values(
		self, context, populated_dotenv, mock_environ
	):
		extra_vars = {"VAR1": "overridden_value"}
		context.load(extra_vars=extra_vars)

		assert context.env_vars.get("VAR1") == "overridden_value"
		assert context.env_vars.get("VAR2") == "value2"

	def test_should_handle_empty_extra_vars_dict(self, context, mock_environ):
		context.load(extra_vars={})
		assert target_env_var_fixture() in context.env_vars

	def test_should_accept_none_values_in_extra_vars(self, context, mock_environ):
		extra_vars = {"VAR1": None, "VAR2": "value2"}
		context.load(extra_vars=extra_vars)

		assert context.env_vars.get("VAR1") is None
		assert context.env_vars.get("VAR2") == "value2"


class TestEnvironmentContextLoadPrecedence:
	def test_should_respect_precedence_order_extra_over_dotenv_over_os(
		self, context, dotenv_path, mock_environ
	):
		with patch("os.environ", {"VAR1": "from_os"}):
			dotenv_path.write_text("VAR1=from_dotenv\nVAR2=from_dotenv\n")
			extra_vars = {"VAR1": "from_extra", "VAR3": "from_extra"}

			context.load(extra_vars=extra_vars)

			assert context.env_vars.get("VAR1") == "from_extra"
			assert context.env_vars.get("VAR2") == "from_dotenv"
			assert context.env_vars.get("VAR3") == "from_extra"

	def test_should_preserve_existing_os_environ_variables(
		self, context, dotenv_path, mock_environ
	):
		with patch("os.environ", {"OS_VAR": "os_value", "ANOTHER_OS_VAR": "another_value"}):
			dotenv_path.write_text("DOTENV_VAR=dotenv_value\n")
			context.load()

			assert context.env_vars.get("OS_VAR") == "os_value"
			assert context.env_vars.get("ANOTHER_OS_VAR") == "another_value"
			assert context.env_vars.get("DOTENV_VAR") == "dotenv_value"


class TestEnvironmentContextMultipleLoads:
	def test_should_update_env_vars_on_subsequent_loads(self, context, dotenv_path, mock_environ):
		dotenv_path.write_text("VAR1=value1\n")
		context.load()
		assert context.env_vars.get("VAR1") == "value1"

		dotenv_path.write_text("VAR1=updated_value\nVAR2=value2\n")
		context.load()
		assert context.env_vars.get("VAR1") == "updated_value"
		assert context.env_vars.get("VAR2") == "value2"

	def test_should_call_pre_load_action_on_each_load(self, trackable_context, mock_environ):
		trackable_context.load()
		trackable_context.load()
		trackable_context.load()

		assert trackable_context.pre_load_call_count == 3
