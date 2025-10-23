from pathlib import Path

from .base_lambda_zip_builder import BaseLambdaZipBuilder
from ..arch_enum import AWSLambdaArchitecture


class PythonZipBuilder(BaseLambdaZipBuilder):
	def build(
		self, project_root: Path, build_dir: Path, output_dir: Path, arch: AWSLambdaArchitecture
	) -> Path:
		raise NotImplementedError("Needs to be implemented to be supported.")
