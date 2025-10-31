from enum import Enum

class StrEnum(str, Enum):
    def __str__(self) -> str:
        return str(self.value)
    
class InfraEnvironment(StrEnum):
	prod = "prod"
	stage = "stage"
	local = "local"


class InfraProviders(StrEnum):
	aws = "aws"
