import click
from pathlib import Path

from .templates_handler import get_template_handler, TEMPLATE_REGISTRY


@click.command("init", help="Initialize a new infrastructure stack from a template, or a blank project.")
@click.option("-t", "--template", "template_name", default=None, help="Template name to use (e.g. 'aws/generic'). Leave empty for a blank project.")
@click.option("-l", "--list-templates", "list_templates", is_flag=True, help="List available templates.")
@click.argument("project_dir", type=click.Path(file_okay=False, dir_okay=True, path_type=Path), default=".")
def template_command(template_name, list_templates, project_dir):
	"""Initialize a new infrastructure stack template."""

	if list_templates:
		click.echo("Available templates:")
		for provider, stacks in TEMPLATE_REGISTRY.items():
			for stack_name in stacks.keys():
				click.echo(f"  - {provider}/{stack_name}")
		return

	infra_dir = Path(project_dir) / "infra"

	if template_name:
		click.echo(f"Initializing stack from template '{template_name}'...")
		try:
			provider, stack = template_name.split("/")
			handler_cls, template_dir = get_template_handler(provider, stack)
			handler = handler_cls(template_dir, infra_dir, stack)
			handler.generate()
			click.echo("Stack initialization complete!")
		except (ValueError, KeyError) as e:
			click.echo(f"Error: Invalid template '{template_name}'. Use --list-templates to see options.", err=True)
			return
	else:
		click.echo("Initializing a blank infrastructure project...")
		infra_dir.mkdir(parents=True, exist_ok=True)
		(infra_dir / "operations").mkdir(exist_ok=True)
		(infra_dir / "environments").mkdir(exist_ok=True)
		# Create empty __init__.py files
		(infra_dir / "operations" / "__init__.py").touch()
		(infra_dir / "environments" / "__init__.py").touch()

		click.echo(f"Blank project created at: {infra_dir}")


if __name__ == "__main__":
	template_command()
