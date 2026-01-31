from enum import Enum


class EFailoverPlanType(str, Enum):
    VMWARE = "Vmware"

    def __str__(self) -> str:
        return str(self.value)
