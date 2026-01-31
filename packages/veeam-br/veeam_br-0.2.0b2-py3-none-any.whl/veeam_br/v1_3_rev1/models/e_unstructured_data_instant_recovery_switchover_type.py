from enum import Enum


class EUnstructuredDataInstantRecoverySwitchoverType(str, Enum):
    AUTO = "Auto"
    MANUAL = "Manual"
    SCHEDULED = "Scheduled"

    def __str__(self) -> str:
        return str(self.value)
