from pathlib import Path
import click
from abc import ABC, abstractmethod

class BaseContextPrompter(ABC):
    def __init__(self, defaults: dict = None):
        """
        Args:
            defaults: Optional dictionary of default values for prompts.
        """
        self.defaults = defaults or {}

    @abstractmethod
    def build_context(self) -> dict:
        """Builds a context dictionary. Must be implemented in subclasses."""
        pass


class GenericContextPrompter(BaseContextPrompter):
    def __init__(self, template_path: Path, defaults: dict = None):
        super().__init__(defaults)
        self.template_path = template_path

    def build_context(self) -> dict:
        """
        Generic prompter: detects variables in a Jinja2 template
        and prompts the user for missing values.
        """
        from jinja2 import Environment, meta

        template_source = self.template_path.read_text()
        env = Environment()
        parsed_content = env.parse(template_source)
        variables = meta.find_undeclared_variables(parsed_content)

        context = {
            var: self.defaults[var] if var in self.defaults else click.prompt(f"Enter value for '{var}'")
            for var in variables
        }

        return context



class NETContextPrompter(BaseContextPrompter):
    def __init__(self, root_dir: Path, defaults: dict = None):
        super().__init__(defaults)
        self.root_dir = root_dir

    def select_csproj(self) -> Path:
        """Scan the root directory for .csproj files and prompt the user to select one."""
        csproj_files = list(self.root_dir.glob("*.csproj"))
        if not csproj_files:
            raise FileNotFoundError(f"No .csproj files found in {self.root_dir}")

        if len(csproj_files) == 1:
            click.echo(f"Found one project: {csproj_files[0].name}")
            return csproj_files[0].stem

        click.echo("Select a project file:")
        for i, file in enumerate(csproj_files, start=1):
            click.echo(f"{i}) {file.name}")

        choice = click.prompt(
            "Enter the number of the project",
            type=click.IntRange(1, len(csproj_files))
        )

        return csproj_files[choice - 1].stem

    def build_context(self) -> dict:
        """Builds a context dictionary including the selected .csproj file."""
        context = dict(self.defaults)
        context['project_name'] = self.select_csproj()
        return context
