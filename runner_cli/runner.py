import sys
import logging
import click
import importlib
import pkgutil
from typing import Dict, Type, Optional, List

from ..base_infra import BaseInfraBuilder
from ..enums import Environment
from .env_builder import EnvBuilder

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def discover_builders(package_name: str = "infra_builders") -> Dict[str, Type[BaseInfraBuilder]]:
    """Dynamically discover all infra builders in the given package."""
    registry: Dict[str, Type[BaseInfraBuilder]] = {}

    try:
        package = importlib.import_module(package_name)
    except ModuleNotFoundError:
        logger.warning(f"No {package_name} package found — no custom builders loaded.")
        return registry

    for _, module_name, _ in pkgutil.iter_modules(package.__path__, package.__name__ + "."):
        module = importlib.import_module(module_name)
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and issubclass(attr, BaseInfraBuilder) and attr is not BaseInfraBuilder:
                registry[attr_name.lower()] = attr

    return registry


def build_env_core(
    project: str,
    environment: Optional[str] = None,
    infra_builders: Optional[List[BaseInfraBuilder]] = None,
):
    env = Environment(environment) if environment else None
    builder = EnvBuilder(project_name=project, environment=env)
    builder.execute(infra_builders=infra_builders)


@click.command()
@click.option("--project", type=str, required=True, help="Project name to build/run")
@click.option(
    "--environment",
    type=click.Choice([m.value for m in Environment], case_sensitive=True),
    default=None,
    help="Deployment environment [local | stage | prod]",
)
@click.option(
    "--builder",
    multiple=True,
    help="Infra builders to run (auto-discovered from infra_builders/)",
)
def build_env_cli(project, environment, builder):
    """CLI entrypoint for building a local infrastructure environment."""
    try:
        registry = discover_builders()
        if builder:
            infra_builders = []
            for name in builder:
                if name not in registry:
                    raise ValueError(f"Builder '{name}' not found. Available: {list(registry.keys())}")
                infra_builders.append(registry[name]())
        else:
            infra_builders = None

        build_env_core(project=project, environment=environment, infra_builders=infra_builders)
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    build_env_cli()
