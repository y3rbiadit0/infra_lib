class InfraError(Exception):
	pass


class ConfigError(InfraError):
	pass


class OpError(InfraError):
	pass


class CycleError(InfraError):
	pass
