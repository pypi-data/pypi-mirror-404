from enum import Enum


class EAccountPermissionType(str, Enum):
    ALLOWEVERYONE = "AllowEveryone"
    ALLOWSELECTED = "AllowSelected"
    DENYEVERYONE = "DenyEveryone"

    def __str__(self) -> str:
        return str(self.value)
