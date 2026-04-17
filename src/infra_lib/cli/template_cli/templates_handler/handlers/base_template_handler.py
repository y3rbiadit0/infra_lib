from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict
import logging

from jinja2 import Environment as JinjaEnvironment, FileSystemLoader

from .....infra.enums import InfraEnvironment
from ..template_file import TemplateFile, VSCodeGenerator, VSCodeLaunchConfig

logger = logging.getLogger(__name__)


class BaseTemplateHandler(ABC):
	environments = [e.value for e in InfraEnvironment]

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
		"""Generate all core + extra infrastructure files"""
		self._create_environments_init()
		self._ensure_infra_gitignore()

		common_files = self._get_common_files()
		for tf in common_files:
			tf.target.parent.mkdir(parents=True, exist_ok=True)
			tf.generate(self.jinja_env)

		logger.info(f"Generated {len(common_files)} shared infrastructure files")

		for env in self.environments:
			self._create_env_init(env)

			files = self._get_env_specific_files(env) + self.get_extra_files(env)

			for tf in files:
				tf.target.parent.mkdir(parents=True, exist_ok=True)
				tf.generate(self.jinja_env)

			logger.info(f"Generated {len(files)} files for environment '{env}'")

		VSCodeGenerator(self.project_root.parent).add_tasks(self.vscode_configurations())
		logger.info("Infrastructure scaffolding completed")

	def _ensure_infra_gitignore(self):
		"""Ensure infra-managed generated files stay untracked."""
		gitignore = self.project_root / ".gitignore"
		entry = ".infra-generated.env\n"

		if gitignore.exists():
			content = gitignore.read_text()
			if entry.strip() in {line.strip() for line in content.splitlines()}:
				return
		else:
			content = ""

		with gitignore.open("a") as f:
			if content and not content.endswith("\n"):
				f.write("\n")
			f.write(entry)

	def _create_env_init(self, infra_environment: str):
		"""
		Create __init__.py inside environment folders (local, stage, prod)
		that imports its environment-specific infra class.
		"""
		env_dir = self.project_root / "environments" / infra_environment
		env_dir.mkdir(parents=True, exist_ok=True)
		init_file = env_dir / "__init__.py"

		import_line = f"from .{infra_environment} import {infra_environment.capitalize()}Context\n"
		init_file.write_text(import_line)

	def _create_environments_init(self):
		"""
		Create infrastructure/__init__.py that imports all environment classes.
		Example:
		    from .local import LocalInfra
		    from .stage import StageInfra
		    from .prod import ProdInfra
		"""
		infra_dir = self.project_root / "environments"
		infra_dir.mkdir(exist_ok=True)
		lines = [f"from .{env} import {env.capitalize()}Context\n" for env in self.environments]
		init_file = infra_dir / "__init__.py"
		init_file.write_text("".join(lines))

	def _get_common_files(self) -> List[TemplateFile]:
		"""Core files that every handler must generate"""
		return [
			TemplateFile(
				source=self.templates_dir / "docker-compose.yml.j2",
				target=self.project_root / "docker-compose.yml",
				context_provider=self.get_docker_context,
			),
			TemplateFile(
				source=self.templates_dir / ".env.j2",
				target=self.project_root / ".env",
				context_provider=lambda: self.get_env_context(self.environments[0]),
			),
		]

	def _get_env_specific_files(self, env: str) -> List[TemplateFile]:
		"""Core files that every handler must generate"""
		env_dir = self.project_root / "environments" / env

		return [
			TemplateFile(
				source=self.templates_dir / "env_context.py.j2",
				target=env_dir / f"{env}.py",
				context_provider=lambda: self.get_infra_context(env),
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

	@abstractmethod
	def vscode_configurations(self) -> List[VSCodeLaunchConfig]:
		pass

	def get_extra_files(self, env: str) -> List[TemplateFile]:
		"""Hook for provider/stack-specific files (default = none)"""
		return []
