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
        # Generate docker-compose.yml
        compose_file = self.project_dir / "docker-compose.yml"
        compose_file.write_text(
            self.render_template(
                Path("templates/docker-compose.yml.j2"),
                services="s3,sqs,lambda,secretsmanager"
            )
        )

        # Generate .env
        env_file = self.project_dir / ".env"
        env_file.write_text(self.render_template(Path("templates/env.j2")))

        # Generate run_cloud.py
        run_file = self.project_dir / "run_cloud.py"
        run_file.write_text(
            self.render_template(Path("templates/run_cloud.py.j2"), project_name=self.project_name)
        )

        # Generate {project_name}_infra.py
        infra_file = self.project_dir / f"{self.project_name}_infra.py"
        infra_file.write_text(
            self.render_template(Path("templates/infra.py.j2"))
        )

        print(f"✅ Generated infra for {self.stack_type} at {self.project_dir}")
