from pathlib import Path
import click
from jinja2 import meta, Environment as JinjaEnvironment


def context_prompter(template_path: Path, defaults: dict = None):
    """Build a context dict for a Jinja2 template by prompting the user for missing variables."""
    defaults = defaults or {}

    template_source = template_path.read_text()
    env = JinjaEnvironment()
    parsed_content = env.parse(template_source)

    variables = meta.find_undeclared_variables(parsed_content)

    context = {
        var: (
            defaults[var]
            if var in defaults
            else click.prompt(
                f"Enter value for '{var}'", default=None, show_default=False
            )
        )
        for var in variables
    }

    return context
