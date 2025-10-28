import abc
import os
from pathlib import Path
from typing import Dict, Optional
from dotenv import dotenv_values

from ...infra.enums import InfraEnvironment


class EnvironmentContext(abc.ABC):
	"""Stores environment-specific configuration.

	Configuration is loaded via the .load() method and stored in the
	env_vars attribute. This class does not modify the global os.environ.

	Attributes:
	    config_dir: The root directory for configuration files.
	    env_vars: A dictionary holding the loaded environment variables.
	"""

	def __init__(self, project_root: Path, environment_dir: Path):
		"""Initializes the EnvironmentContext.

		Args:
		    config_dir: The root directory for configuration files.
		"""
		self.project_root: Path = project_root
		self.environment_dir: Path = environment_dir
		self.env_vars: Dict[str, str] = {}
		super().__init__()

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
		return self.environment_dir.parent / self.env().value / ".env"

	def pre_load_action(self):
		"""A hook for subclasses to run logic before config is loaded.

		This can be overridden by subclasses to perform actions like
		fetching secrets or authenticating to a service.
		"""
		pass

	def load(self, extra_vars: Optional[Dict[str, str]] = None):
		"""Loads configuration into the self.env_vars dictionary.

		This method is the main entry point for loading configuration.
		It calls pre_load_action, determines the .env path, loads the
		values, and sets the TARGET_ENV variable.
		"""
		self.pre_load_action()
		dotenv_path = self.get_dotenv_path()
		loaded_vars = os.environ.copy()

		if dotenv_path.exists():
			dotenv_vars = dotenv_values(dotenv_path)
			loaded_vars.update(dotenv_vars)

		loaded_vars["TARGET_ENV"] = self.env().value

		if extra_vars:
			loaded_vars.update(extra_vars)

		self.env_vars = loaded_vars
		os.environ.update(loaded_vars)

	def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
		"""Safe getter for accessing configuration values.

		Args:
		    key: The name of the environment variable to retrieve.
		    default: The value to return if the key is not found.

		Returns:
		    The value of the environment variable, or the default.
		"""
		return self.env_vars.get(key, default)
