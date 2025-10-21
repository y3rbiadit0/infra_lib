import subprocess
import pytest
from unittest.mock import patch, MagicMock
from infra_lib.utils import run_command


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
