import click
from pathlib import Path

from .templates_handler import get_template_handler


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

    project_dir = Path(".")
    
    handler_cls, template_dir = get_template_handler(provider, stack)
    handler = handler_cls(template_dir, project_dir, stack)
    handler.generate()
    
    click.echo("Stack initialization complete!")


if __name__ == "__main__":
    template_cli()
