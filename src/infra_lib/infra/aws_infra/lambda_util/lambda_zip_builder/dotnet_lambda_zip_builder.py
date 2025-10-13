from pathlib import Path

from .....utils import run_command
from .base_lambda_zip_builder import BaseLambdaZipBuilder


class DotnetZipBuilder(BaseLambdaZipBuilder):
	def build(self, project_root: Path, build_dir: Path, output_dir: Path) -> Path:
		project_files = list(project_root.glob("*.csproj"))
		if not project_files:
			raise FileNotFoundError(f"No .csproj found in {project_root}")
		project_file = project_files[0]

		output_dir.mkdir(parents=True, exist_ok=True)
		build_cmd = [
			"dotnet",
			"publish",
			str(project_file),
			"-c",
			"Release",
			"-o",
			str(build_dir),
		]

		run_command(" ".join(build_cmd))
		return self._zip_folder(
			project_root=project_root, build_dir=build_dir, output_dir=output_dir
		)
