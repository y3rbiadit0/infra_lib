import subprocess
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock
from infra_lib.utils import run_command
from infra_lib.utils.docker_compose import DockerCompose, ComposeSettings
from infra_lib import InfraEnvironment, EnvironmentContext


def test_run_command_success():
	mock_result = MagicMock()
	mock_result.returncode = 0

	with patch("subprocess.run", return_value=mock_result) as mock_run:
		ret = run_command("echo hello", check=True)
		assert ret == 0
		mock_run.assert_called_once_with(
			"echo hello", shell=True, stdout=None, stderr=None, stdin=None, env=None
		)


def test_run_command_failure_check_true():
	mock_result = MagicMock()
	mock_result.returncode = 1

	with patch("subprocess.run", return_value=mock_result):
		with pytest.raises(RuntimeError):
			run_command("false", check=True)


def test_run_command_failure_check_false():
	mock_result = MagicMock()
	mock_result.returncode = 1

	with patch("subprocess.run", return_value=mock_result):
		ret = run_command("false", check=False)
		assert ret == mock_result.returncode


def test_run_command_no_output():
	mock_result = MagicMock()
	mock_result.returncode = 0

	with patch("subprocess.run", return_value=mock_result) as mock_run:
		ret = run_command("echo hello", show_output=False)
		assert ret == 0
		mock_run.assert_called_once_with(
			"echo hello",
			shell=True,
			stdout=subprocess.DEVNULL,
			stderr=subprocess.DEVNULL,
			stdin=None,
			env=None,
		)


def test_docker_compose_down_runs_single_command(tmp_path: Path):
	compose_file = tmp_path / "docker-compose.yml"
	compose_file.write_text("services: {}\n")
	env_context = MagicMock(spec=EnvironmentContext)
	env_context.env_vars = {"TARGET_ENV": "local"}
	settings = ComposeSettings(
		environment=InfraEnvironment.local,
		compose_file=compose_file,
		custom_profiles=["api"],
		compose_name="infra-test",
	)
	compose = DockerCompose(settings, env_context)

	with patch("infra_lib.utils.docker_compose.run_command") as mock_run_command:
		compose.down(remove_volumes=True)

		mock_run_command.assert_called_once_with(
			f"docker compose -p infra-test -f {compose_file} --profile local --profile api down -v",
			env_vars=env_context.env_vars,
		)


def test_docker_compose_down_skips_volume_flag_when_disabled(tmp_path: Path):
	compose_file = tmp_path / "docker-compose.yml"
	compose_file.write_text("services: {}\n")
	env_context = MagicMock(spec=EnvironmentContext)
	env_context.env_vars = {"TARGET_ENV": "local"}
	settings = ComposeSettings(
		environment=InfraEnvironment.local,
		compose_file=compose_file,
		custom_profiles=[],
	)
	compose = DockerCompose(settings, env_context)

	with patch("infra_lib.utils.docker_compose.run_command") as mock_run_command:
		compose.down(remove_volumes=False)

		mock_run_command.assert_called_once_with(
			f"docker compose -p infra -f {compose_file} --profile local down",
			env_vars=env_context.env_vars,
		)
