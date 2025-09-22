import click
from .runner_cli import run_infra
from .template_cli import template_cli


@click.group()
def infra_cli():
    """Infra CLI for creating and managing infrastructure templates."""
    pass


# Register commands
infra_cli.add_command(run_infra)
infra_cli.add_command(template_cli)

if __name__ == "__main__":
    infra_cli()
