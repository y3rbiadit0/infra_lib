import os
from pathlib import Path
import sys
import logging
import click

from .env_builder import EnvBuilder
from ...enums import InfraEnvironment

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@click.command("run")
@click.option(
	"--project",
	type=str,
	required=True,
	help="Project name to run",
)
def run_infra(project: str, environment: str):
	"""CLI runner to spin up Docker Compose and deploy environment-specific infrastructure."""
	try:
		project_root = Path.joinpath(Path(os.getcwd()).resolve(), "infrastructure")
		env = InfraEnvironment(environment)
		builder = EnvBuilder(project_name=project, environment=env, project_root=project_root)
		builder.execute()
		logger.info("✅ Environment deployed successfully!")

	except Exception as e:
		logger.error(f"❌ Error deploying environment: {e} {e.__traceback__}")
		sys.exit(1)


if __name__ == "__main__":
	run_infra()