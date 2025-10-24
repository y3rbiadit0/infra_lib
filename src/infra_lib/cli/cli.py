import click

from .runner_cli import run_infra, deploy_infra
from .template_cli import template_cli
from .__version__ import __version__


@click.group()
@click.version_option(version=__version__, prog_name="infra-cli")
def infra_cli():
	"""Infra CLI for creating and managing infrastructure templates."""
	pass


infra_cli.add_command(template_cli)
infra_cli.add_command(run_infra)
infra_cli.add_command(deploy_infra)

if __name__ == "__main__":
	infra_cli()
