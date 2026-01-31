from enum import Enum


class EFlrMountModeServerType(str, Enum):
    HELPERAPPLIANCE = "HelperAppliance"
    HELPERHOST = "HelperHost"
    MOUNTSERVER = "MountServer"
    ORIGINALHOST = "OriginalHost"

    def __str__(self) -> str:
        return str(self.value)
