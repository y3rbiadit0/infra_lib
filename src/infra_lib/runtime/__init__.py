import os
from pathlib import Path
from typing import Optional
from ..infra.enums import InfraEnvironment


def load_env(env: Optional[InfraEnvironment] = None, project_root: Optional[Path] = None) -> None:
	"""Load environment variables from .env file and set TARGET_ENV.

	This function is useful for local development/debugging without going
	through the CLI runner. It loads .env from infra/environments/{env}/.env
	and updates os.environ.

	Args:
	    env: The environment to load. If None, auto-detects by checking
	         which environment directory exists under infra/environments/.
	         If multiple exist, raises ValueError.
	    project_root: Path to the project root. Defaults to current directory.
	                  Should be the parent of the infra/ directory.

	Raises:
	    ValueError: If environment cannot be determined or .env file not found.
	    FileNotFoundError: If the environment .env file doesn't exist.
	"""
	project_root = project_root or Path.cwd()
	infra_dir = project_root / "infra"

	if env is None:
		env = _auto_detect_env(infra_dir)

	env_dir = infra_dir / "environments" / env.value
	dotenv_file = env_dir / ".env"

	if not dotenv_file.exists():
		raise FileNotFoundError(
			f".env file not found at {dotenv_file}. Cannot load environment '{env.value}'"
		)

	from dotenv import dotenv_values

	loaded_vars = dotenv_values(dotenv_file)
	os.environ["TARGET_ENV"] = env.value
	os.environ.update(loaded_vars)


def _auto_detect_env(infra_dir: Path) -> InfraEnvironment:
	"""Auto-detect environment by checking which environment directory exists."""
	envs_dir = infra_dir / "environments"

	if not envs_dir.is_dir():
		raise ValueError(
			f"Cannot auto-detect environment: {envs_dir} does not exist. "
			f"Either specify the environment explicitly or run 'infra-cli run <env>' first."
		)

	found_envs = []
	for env in InfraEnvironment:
		env_path = envs_dir / env.value
		if env_path.is_dir():
			found_envs.append(env)

	if not found_envs:
		raise ValueError(
			f"No environment directories found in {envs_dir}. "
			f"Expected one of: {[e.value for e in InfraEnvironment]}"
		)

	if len(found_envs) > 1:
		if InfraEnvironment.local in found_envs:
			return InfraEnvironment.local
		raise ValueError(
			f"Multiple environments found: {[e.value for e in found_envs]}. "
			f"Please specify the environment explicitly."
		)

	return found_envs[0]


def get_env() -> InfraEnvironment:
	"""Get the current environment from TARGET_ENV environment variable.

	Returns:
	    InfraEnvironment: The current environment (local, stage, or prod)

	Raises:
	    ValueError: If TARGET_ENV is not set or has an invalid value
	"""
	target = os.environ.get("TARGET_ENV")
	if not target:
		raise ValueError("TARGET_ENV environment variable is not set")

	try:
		return InfraEnvironment(target)
	except ValueError:
		valid_values = [e.value for e in InfraEnvironment]
		raise ValueError(f"Invalid TARGET_ENV value: '{target}'. Must be one of: {valid_values}")


def get_env_vars(key: Optional[str] = None) -> Optional[str]:
	"""Get environment variables, optionally filtering by a specific key.

	Args:
	    key: Optional specific key to retrieve. If None, returns all env vars
	         as a dict. If provided, returns just that value or None.

	Returns:
	    If key is provided: the value for that key, or None if not found.
	    If key is None: dict of all environment variables (os.environ copy).

	Raises:
	    ValueError: If TARGET_ENV is not set (when key is provided).
	"""
	target = os.environ.get("TARGET_ENV")
	if not target:
		raise ValueError("TARGET_ENV environment variable is not set")

	if key is None:
		return dict(os.environ)

	return os.environ.get(key)
