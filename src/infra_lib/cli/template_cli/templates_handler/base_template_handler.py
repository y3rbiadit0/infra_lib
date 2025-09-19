from pathlib import Path
from abc import ABC, abstractmethod
from jinja2 import Environment as JinjaEnvironment, FileSystemLoader
from typing import Dict
import logging

from ....enums import Environment

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class BaseTemplateHandler(ABC):
    """
    Abstract base handler to scaffold infrastructure templates for all environments:
    - infra_<env>.py
    - .env files
    - docker-compose.yml
    - provider-specific files
    """

    environments = [e.value for e in Environment]

    def __init__(
        self,
        templates_dir: Path,
        project_root: Path,
        stack_type: str,
        provider: str = "",
    ):
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
        """Generate all infrastructure artifacts"""
        self._generate_infra_classes()
        self._generate_env_files()
        self._generate_docker_compose()
        self._generate_provider_specific()
        logger.info("Infrastructure scaffolding complete!")

    def _generate_infra_classes(self):
        template = self.jinja_env.get_template("infra_class.py.j2")
        for env in self.environments:
            context = self.get_infra_context(env)
            output_dir = self.project_root / "infrastructure" / env
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / f"infra_{env}.py"
            output_file.write_text(template.render(context))
            logger.info(f"Generated {output_file}")

    def _generate_env_files(self):
        template = self.jinja_env.get_template(".env.j2")
        for env in self.environments:
            context = self.get_env_context(env)
            output_dir = self.project_root / "infrastructure" / env
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / ".env"
            output_file.write_text(template.render(context))
            logger.info(f"Generated {output_file}")

    def _generate_docker_compose(self):
        template = self.jinja_env.get_template("docker-compose.yml.j2")
        context = self.get_docker_context()
        output_file = self.project_root / "infrastructure" / "docker-compose.yml"
        output_file.write_text(template.render(context))
        logger.info(f"Generated {output_file}")

    def _generate_provider_specific(self):
        """Copy provider-specific templates (e.g., secrets.json)"""
        if not self.provider:
            return
        provider_folder = (
            self.project_root / "infrastructure" / f"{self.provider}_config"
        )
        provider_folder.mkdir(parents=True, exist_ok=True)
        
        template_provider_folder = self.templates_dir / f"{self.provider}_config"
        if template_provider_folder.exists():
            for file_path in template_provider_folder.iterdir():
                target_file = provider_folder / file_path.name
                target_file.write_text(file_path.read_text())
                print(f"Generated {target_file}")

    @abstractmethod
    def get_infra_context(self, env: str) -> Dict:
        """Return context Dict for infra_class.py.j2 template"""
        pass

    @abstractmethod
    def get_env_context(self, env: str) -> Dict:
        """Return context Dict for .env.j2 template"""
        pass

    @abstractmethod
    def get_docker_context(self) -> Dict:
        """Return context Dict for docker-compose.yml.j2 template"""
        pass
