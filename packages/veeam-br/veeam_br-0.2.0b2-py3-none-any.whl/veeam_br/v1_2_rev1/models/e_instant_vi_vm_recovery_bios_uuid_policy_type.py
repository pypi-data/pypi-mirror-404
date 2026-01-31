from enum import Enum


class EInstantViVmRecoveryBiosUuidPolicyType(str, Enum):
    GENERATENEW = "generateNew"
    PRESERVE = "preserve"

    def __str__(self) -> str:
        return str(self.value)
