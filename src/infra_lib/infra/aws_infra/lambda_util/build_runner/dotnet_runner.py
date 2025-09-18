from pathlib import Path

from .....utils import run_command
from .base_runner import BuildRunner


class DotnetBuildRunner(BuildRunner):
    def build(self, project_path: Path, output_dir: Path) -> None:
        project_files = list(project_path.glob("*.csproj"))
        if not project_files:
            raise FileNotFoundError(f"No .csproj found in {project_path}")
        project_file = project_files[0]

        output_dir.mkdir(parents=True, exist_ok=True)
        build_cmd = [
            "dotnet",
            "publish",
            str(project_file),
            "-c",
            "Release",
            "-o",
            str(output_dir),
        ]
        run_command(" ".join(build_cmd))
