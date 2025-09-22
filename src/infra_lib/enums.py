from enum import StrEnum


class InfraEnvironment(StrEnum):
    prod = "prod"
    stage = "stage"
    local = "local"


class SupportedStack(StrEnum):
    net8 = "net8"


class InfraProviders(StrEnum):
    aws = "aws"
