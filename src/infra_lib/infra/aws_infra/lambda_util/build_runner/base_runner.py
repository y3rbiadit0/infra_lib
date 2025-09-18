from abc import ABC, abstractmethod
from pathlib import Path

class BuildRunner(ABC):
    @abstractmethod
    def build(self, project_path: Path, output_dir: Path) -> None:
        """Builds the project and outputs to the given directory."""
        pass
