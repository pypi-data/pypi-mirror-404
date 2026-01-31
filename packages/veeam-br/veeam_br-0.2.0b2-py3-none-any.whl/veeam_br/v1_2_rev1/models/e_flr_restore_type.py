from enum import Enum


class EFlrRestoreType(str, Enum):
    KEEP = "Keep"
    OVERWRITE = "Overwrite"
    PERMISSIONONLY = "PermissionOnly"

    def __str__(self) -> str:
        return str(self.value)
