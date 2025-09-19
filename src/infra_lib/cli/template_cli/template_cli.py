import click
from pathlib import Path

from .infra_generator import InfraGenerator


@click.command("init")
@click.option(
    "--stack", required=True, type=str, help="Type of stack to initialize (e.g., .net8)"
)
@click.option(
    "--provider", required=True, type=str, help="Cloud provider (e.g., aws, azure)"
)
def template_cli(stack, provider):
    """Initialize a new infrastructure stack template."""
    click.echo(f"Initializing stack '{stack}' for provider '{provider}'...")

    # TODO: Add template creation logic here
    # For example:
    # - Create folder structure
    # - Add boilerplate files for Lambda, API Gateway, etc.
    # - Generate default configuration files

    project_dir = Path(".")
    project_dir.mkdir(exist_ok=True)

    generator = InfraGenerator(project_dir, "", stack_type=stack)
    generator.generate()
    click.echo("Stack initialization complete!")


if __name__ == "__main__":
    template_cli()
