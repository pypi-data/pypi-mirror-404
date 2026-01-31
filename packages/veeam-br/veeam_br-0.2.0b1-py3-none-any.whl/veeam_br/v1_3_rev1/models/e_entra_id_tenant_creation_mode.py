from enum import Enum


class EEntraIDTenantCreationMode(str, Enum):
    EXISTINGACCOUNT = "ExistingAccount"
    NEWACCOUNT = "NewAccount"

    def __str__(self) -> str:
        return str(self.value)
