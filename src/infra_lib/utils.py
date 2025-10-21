import subprocess


def run_command(cmd: str, check=True, show_output: bool = True, stdin=None, env_vars=None) -> int:
	"""Run a shell command and optionally check for errors."""
	stdout = None if show_output else subprocess.DEVNULL
	stderr = None if show_output else subprocess.DEVNULL

	result = subprocess.run(
		cmd, shell=True, stdout=stdout, stderr=stderr, stdin=stdin, env=env_vars
	)
	if check and result.returncode != 0:
		raise RuntimeError(f"Command failed: '{cmd}'")
	return result.returncode
