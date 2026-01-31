from enum import Enum


class ECloudCredentialsType(str, Enum):
    AMAZON = "Amazon"
    AZURECOMPUTE = "AzureCompute"
    AZURESTORAGE = "AzureStorage"
    GOOGLE = "Google"
    GOOGLESERVICE = "GoogleService"

    def __str__(self) -> str:
        return str(self.value)
