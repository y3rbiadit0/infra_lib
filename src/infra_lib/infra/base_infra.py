from abc import ABC

from infra_lib.infra.env_context import EnvironmentContext


class BaseInfraProvider(ABC):
	def __init__(
		self,
		env_context: EnvironmentContext,
	):
		self.env_context = env_context
