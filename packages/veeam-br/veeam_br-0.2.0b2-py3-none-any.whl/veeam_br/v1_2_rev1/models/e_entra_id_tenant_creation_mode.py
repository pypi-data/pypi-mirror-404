from enum import Enum


class EEntraIDTenantCreationMode(str, Enum):
    EXISTINGACCOUNT = "existingAccount"
    NEWACCOUNT = "newAccount"

    def __str__(self) -> str:
        return str(self.value)
