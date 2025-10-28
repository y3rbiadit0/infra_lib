from abc import ABC
import logging

from infra_lib.infra.env_context import EnvironmentContext

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class BaseInfraProvider(ABC):
	def __init__(
		self,
		env_context: EnvironmentContext,
	):
		self.env_context = env_context
