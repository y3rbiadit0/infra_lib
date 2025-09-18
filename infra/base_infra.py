from abc import ABC, abstractmethod
from pathlib import Path
import logging
from typing import Dict

from ..enums import Environment

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class BaseInfraBuilder(ABC):
    """Base class for managing project infrastructure across cloud providers.

    This class defines the structure and required methods for provider-specific
    infrastructure builders. It serves as the common entry point for deploying
    infrastructure using cloud-specific utilities.

    Attributes:
        env_vars (Dict[str, str]): Environment variables used for deployment.
        environment (Environment): Target deployment environment (e.g., local, stage, prod).
    """

    env_vars: Dict[str, str]
    environment: Environment

    def __init__(
        self,
        infrastructure_dir: Path,
        projects_dir: Path,
        environment: Environment,
        env_vars: Dict[str, str],
    ):
        """Initializes the BaseInfraBuilder with project paths and environment.

        Args:
            infrastructure_dir (Path): Path to the infrastructure configuration directory.
            projects_dir (Path): Path to the project source directories.
            environment (Environment): Deployment environment (local, stage, prod, etc.).
            env_vars (Dict[str, str]): Environment variables used for deployment.
        """
        self.environment = environment
        self.infrastructure_dir = infrastructure_dir
        self.projects_dir = projects_dir
        self.env_vars = env_vars

    def build(self):
        """Implement project-specific deployment logic.

        Raises:
            NotImplementedError: Must implement provider-specific infrastructure setup.
        """
        raise NotImplementedError("Must implement your own infrastructure setup.")
