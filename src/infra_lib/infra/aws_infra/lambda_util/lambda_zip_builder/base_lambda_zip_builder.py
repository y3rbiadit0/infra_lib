from abc import ABC, abstractmethod
import logging
from pathlib import Path
import zipfile

logger = logging.getLogger(__name__)


class BaseLambdaZipBuilder(ABC):
	@abstractmethod
	def build(self, project_root: Path, build_dir: Path, output_dir: Path) -> Path:
		"""Builds the project and outputs to the given directory.

		Returns: Path to lambda zipfile
		"""
		pass

	def _zip_folder(self, project_root: Path, build_dir: Path, output_dir: Path) -> Path:
		zip_path = output_dir / f"{project_root.name}.zip"
		with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
			for file_path in build_dir.rglob("*"):
				zipf.write(file_path, arcname=file_path.relative_to(build_dir))
		return zip_path
