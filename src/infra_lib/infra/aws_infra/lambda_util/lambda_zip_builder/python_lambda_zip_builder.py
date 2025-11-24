from pathlib import Path
import shutil
from .....utils import run_command
from .base_lambda_zip_builder import BaseLambdaZipBuilder
from ..arch_enum import AWSLambdaArchitecture


class PythonZipBuilder(BaseLambdaZipBuilder):
	def build(
		self, project_root: Path, build_dir: Path, output_dir: Path, arch: AWSLambdaArchitecture
	) -> Path:
		requirements_path = project_root / "requirements.txt"

		shutil.copytree(project_root, build_dir, dirs_exist_on_ok=True)

		if requirements_path.exists():
			run_command(f"pip install -r {requirements_path} -t {build_dir}")

		return self._zip_folder(
			project_root=project_root, build_dir=build_dir, output_dir=output_dir
		)
