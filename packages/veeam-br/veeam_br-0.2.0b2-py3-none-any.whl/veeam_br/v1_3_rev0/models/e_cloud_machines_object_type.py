from enum import Enum


class ECloudMachinesObjectType(str, Enum):
    MACHINE = "Machine"
    REGION = "Region"
    TAG = "Tag"

    def __str__(self) -> str:
        return str(self.value)
