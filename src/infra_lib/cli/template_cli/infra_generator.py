from pathlib import Path
from jinja2 import Template

class InfraGenerator:
    def __init__(self, project_dir: Path, project_name: str, stack_type: str):
        self.project_dir = project_dir
        self.project_name = project_name
        self.stack_type = stack_type

    def render_template(self, template_path: Path, **kwargs):
        content = Template(template_path.read_text()).render(**kwargs)
        return content

    def generate(self):
        pass