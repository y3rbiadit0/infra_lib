import abc
import os
from pathlib import Path
from typing import Dict, Optional

from dotenv import dotenv_values

from ...infra.enums import InfraEnvironment


class EnvironmentContext(abc.ABC):
	"""Stores environment-specific configuration.

	Configuration is loaded via the .load() method and stored in
	container_env_vars and host_env_vars. This class updates global os.environ.

	Attributes:
	    config_dir: The root directory for configuration files.
	    container_env_vars: The environment variables for containers.
	    host_env_vars: The environment variables used for host subprocesses.
	"""

	def __init__(self, project_root: Path, environment_dir: Path):
		"""Initializes the EnvironmentContext.

		Args:
		    config_dir: The root directory for configuration files.
		"""
		self.project_root: Path = project_root
		self.environment_dir: Path = environment_dir
		self._container_env_vars: Dict[str, str] = {}
		self._host_env_vars: Dict[str, str] = {}
		super().__init__()

	@property
	def container_env_vars(self) -> Dict[str, str]:
		return self._container_env_vars.copy()

	@property
	def host_env_vars(self) -> Dict[str, str]:
		return self._host_env_vars.copy()

	@abc.abstractmethod
	def env(self) -> InfraEnvironment:
		"""The specific environment (e.g., local, staging)."""
		pass

	def get_dotenv_path(self) -> Path:
		"""Gets the path to the specific .env file for the subclass.

		Subclasses must implement this to point to their specific .env file.
		e.g., return self.config_dir / ".env.local"

		Returns:
		    A Path object to the .env file.
		"""
		return self.environment_dir / ".env"

	def get_dotenv_paths(self) -> list[Path]:
		"""Gets the ordered list of dotenv files to load for this context."""
		return [self.get_dotenv_path()]

	def pre_load_action(self):
		"""A hook for subclasses to run logic before config is loaded.

		This can be overridden by subclasses to perform actions like
		fetching secrets or authenticating to a service.
		"""
		pass

	def _build_container_env_vars(
		self, extra_vars: Optional[Dict[str, str]] = None
	) -> Dict[str, str]:
		container_env_vars: Dict[str, str] = {}

		for dotenv_path in self.get_dotenv_paths():
			if dotenv_path.exists():
				dotenv_vars = {
					key: value
					for key, value in dotenv_values(dotenv_path).items()
					if value is not None
				}
				container_env_vars.update(dotenv_vars)

		container_env_vars["TARGET_ENV"] = self.env().value

		if extra_vars:
			container_env_vars.update(extra_vars)

		return container_env_vars

	def _build_host_env_vars(self, container_env_vars: Dict[str, str]) -> Dict[str, str]:
		host_env_vars = os.environ.copy()
		host_env_vars.update(container_env_vars)
		return host_env_vars

	def load(self, extra_vars: Optional[Dict[str, str]] = None):
		"""Loads configuration into container and host environment dictionaries.

		This method is the main entry point for loading configuration.
		It calls pre_load_action, determines the .env path, loads the
		values, and sets the TARGET_ENV variable.
		"""
		self.pre_load_action()

		self._container_env_vars = self._build_container_env_vars(extra_vars)
		self._host_env_vars = self._build_host_env_vars(self.container_env_vars)
		os.environ.update(self._host_env_vars)

	def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
		"""Safe getter for accessing configuration values.

		Args:
		    key: The name of the environment variable to retrieve.
		    default: The value to return if the key is not found.

		Returns:
		    The value of the environment variable, or the default.
		"""
		return self._container_env_vars.get(key, default)
