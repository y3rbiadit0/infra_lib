from pathlib import Path
from .base_lambda_zip_builder import BaseLambdaZipBuilder


class PythonZipBuilder(BaseLambdaZipBuilder):
	def build(self, project_root: Path, build_dir: Path, output_dir: Path) -> Path:
		raise NotImplementedError("Needs to be implemented to be supported.")
