from enum import Enum


class EEntraIdTenantRestoreSessionLogStyle(str, Enum):
    BOLD = "Bold"
    GRAY = "Gray"
    NONE = "None"
    TAIL = "Tail"

    def __str__(self) -> str:
        return str(self.value)
