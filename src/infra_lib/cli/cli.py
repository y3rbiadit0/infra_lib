import click
from .runner_cli import run_infra, deploy_infra
from .template_cli import template_cli


@click.group()
def infra_cli():
	"""Infra CLI for creating and managing infrastructure templates."""
	pass


infra_cli.add_command(template_cli)
infra_cli.add_command(run_infra)
infra_cli.add_command(deploy_infra)

if __name__ == "__main__":
	infra_cli()
