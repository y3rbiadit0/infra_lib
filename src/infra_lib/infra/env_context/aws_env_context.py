import abc
from pathlib import Path
from . import EnvironmentContext


class AWSEnvironmentContext(EnvironmentContext, abc.ABC):
	def aws_config_dir(self) -> Path:
		return self.environment_dir / "aws_config"
