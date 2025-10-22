from enum import StrEnum


class InfraEnvironment(StrEnum):
	prod = "prod"
	stage = "stage"
	local = "local"


class InfraProviders(StrEnum):
	aws = "aws"
