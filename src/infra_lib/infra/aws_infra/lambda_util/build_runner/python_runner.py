from pathlib import Path
from .base_runner import BuildRunner


class PythonBuildRunner(BuildRunner):
	def build(self, project_path: Path, output_dir: Path) -> None:
		raise NotImplementedError("Needs to be implemented to be supported.")
