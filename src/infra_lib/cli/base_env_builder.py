import os
import sys
import logging
import importlib.util
from functools import cached_property
from pathlib import Path
from typing import Dict, Optional, Type

from dotenv import load_dotenv

from ..enums import InfraEnvironment
from ..infra.base_infra import BaseInfra

logger = logging.getLogger(__name__)


class BaseEnvBuilder:
    """
    Base class for builders that interact with environment-specific folders.
    Handles common logic for path resolution, environment variable loading,
    and dynamic discovery of infrastructure classes.
    """
    project_name: str
    env_vars: Dict[str, str]

    def __init__(
        self,
        project_name: str,
        project_root: Optional[Path],
        environment: Optional[InfraEnvironment] = None,
    ):
        """
        Args:
            project_name (str): Name of the project.
            environment (InfraEnvironment, optional): The target environment.
                Defaults to TARGET_ENV environment variable or 'local'.
            project_root (Path, optional): The root 'infrastructure' folder.
                Defaults to '<current_working_dir>/infrastructure'.
        """
        self.project_name = project_name
        self.project_root = project_root or Path.joinpath(Path(os.getcwd()).resolve(), "infrastructure")

        if environment is None:
            env_value = os.environ.get("TARGET_ENV", InfraEnvironment.local.value)
            self.environment = InfraEnvironment(env_value)
        else:
            self.environment = environment

        self.env_vars = self._load_env()


    @property
    def environment_dir(self) -> Path:
        env_dir = self.project_root / self.environment.value
        if not env_dir.exists():
            raise FileNotFoundError(f"Environment folder {env_dir} not found")
        return env_dir

    def _load_env(self) -> Dict[str, str]:
        dotenv_path = next(self.environment_dir.glob(".env*"), None)
        if dotenv_path is None:
            raise FileNotFoundError(f"No .env file found in {self.environment_dir}")
        
        load_dotenv(dotenv_path)
        
        env = os.environ.copy()
        env["PROJECT_NAME"] = self.project_name
        env["TARGET_ENV"] = self.environment.value
        return env

    @cached_property
    def infra_class(self) -> BaseInfra:
        """Loads and instantiates the environment-specific infrastructure class."""
        infra_class = self._load_infra_class()
        return infra_class(
            infrastructure_dir=self.project_root,
            project_root=self.project_root.parent,
            project_name=self.project_name,
            environment=self.environment,
            env_vars=self.env_vars,
        )

    def _load_infra_class(self) -> Type[BaseInfra]:
        """
        Dynamically loads and returns the environment-specific infrastructure
        class type from the 'infrastructure/__init__.py' file.
        """
        module_path = self.project_root / "__init__.py"
        if not module_path.is_file():
            raise FileNotFoundError(f"Infrastructure entrypoint not found at {module_path}")

        spec = importlib.util.spec_from_file_location("infrastructure", module_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules["infrastructure"] = module
        spec.loader.exec_module(module)

        class_name = f"{self.environment.value.capitalize()}Infra"
        if not hasattr(module, class_name):
            raise AttributeError(f"Class '{class_name}' not found in {module_path}")
        
        infra_class = getattr(module, class_name)
        if not issubclass(infra_class, BaseInfra):
            logger.error(f"Class '{infra_class.__name__}' is not a valid infra class.")
            logger.error("Please inherit from 'BaseInfra' to enable tasks.")
            sys.exit(1)

        return infra_class  