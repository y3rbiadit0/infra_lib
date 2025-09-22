from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict
import logging

from jinja2 import Environment as JinjaEnvironment, FileSystemLoader

from .....enums import InfraEnvironment
from ..template_file.template_file import TemplateFile

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class BaseTemplateHandler(ABC):
    environments = [e.value for e in InfraEnvironment]

    def __init__(self, templates_dir: Path, project_root: Path, stack_type: str, provider: str = ""):
        self.templates_dir = templates_dir
        self.project_root = project_root
        self.stack_type = stack_type
        self.provider = provider.lower()
        self.jinja_env = JinjaEnvironment(
            loader=FileSystemLoader(str(self.templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def generate(self):
        """Generate all core + extra infrastructure files"""
        self._create_infrastructure_init()

        for env in self.environments:
            logger.info(f"Generating for {env}...")
            
            self._create_env_init(env)
            
            files = self._get_core_files(env) + self.get_extra_files(env)

            for tf in files:
                tf.target.parent.mkdir(parents=True, exist_ok=True)
                tf.generate(self.jinja_env)
                logger.info(f"Generated {tf.target}")

        logger.info("Infrastructure scaffolding complete!")

    def _create_env_init(self, env: str):
        """
        Create __init__.py inside environment folders (local, stage, prod)
        that imports its environment-specific infra class.
        """
        env_dir = self.project_root / "infrastructure" / env
        env_dir.mkdir(parents=True, exist_ok=True)
        init_file = env_dir / "__init__.py"

        import_line = f"from .infra_{env} import {env.capitalize()}Infra\n"
        init_file.write_text(import_line)
        logger.info(f"Created {init_file} with import for {env}")


    def _create_infrastructure_init(self):
        """
        Create infrastructure/__init__.py that imports all environment classes.
        Example:
            from .local import LocalInfra
            from .stage import StageInfra
            from .prod import ProdInfra
        """
        infra_dir = self.project_root / "infrastructure"
        infra_dir.mkdir(exist_ok=True)
        lines = [
            f"from .{env} import {env.capitalize()}Infra\n"
            for env in self.environments
        ]
        init_file = infra_dir / "__init__.py"
        init_file.write_text("".join(lines))
        logger.info(f"Created {init_file} importing all environments")



    def _get_core_files(self, env: str) -> List[TemplateFile]:
        """Core files that every handler must generate"""
        env_dir = self.project_root / "infrastructure" / env

        return [
            TemplateFile(
                source=self.templates_dir / "infra_class.py.j2",
                target=env_dir / f"infra_{env}.py",
                context_provider=lambda: self.get_infra_context(env),
            ),
            TemplateFile(
                source=self.templates_dir / ".env.j2",
                target=env_dir / ".env",
                context_provider=lambda: self.get_env_context(env),
            ),
            TemplateFile(
                source=self.templates_dir / "docker-compose.yml.j2",
                target=self.project_root / "infrastructure" / "docker-compose.yml",
                context_provider=self.get_docker_context,
            ),
        ]

    @abstractmethod
    def get_infra_context(self, env: InfraEnvironment) -> Dict:
        pass

    @abstractmethod
    def get_env_context(self, env: InfraEnvironment) -> Dict:
        pass

    @abstractmethod
    def get_docker_context(self) -> Dict:
        pass

    def get_extra_files(self, env: str) -> List[TemplateFile]:
        """Hook for provider/stack-specific files (default = none)"""
        return []
