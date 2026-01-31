from enum import Enum


class EAzureComputeCredentialsCreationMode(str, Enum):
    EXISTINGACCOUNT = "ExistingAccount"
    NEWACCOUNT = "NewAccount"

    def __str__(self) -> str:
        return str(self.value)
