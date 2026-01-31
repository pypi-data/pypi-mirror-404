from enum import Enum


class EInstantViVmRecoveryBiosUuidPolicyType(str, Enum):
    GENERATENEW = "GenerateNew"
    PRESERVE = "Preserve"

    def __str__(self) -> str:
        return str(self.value)
