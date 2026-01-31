from enum import Enum


class EAzureComputeCredentialsDeploymentType(str, Enum):
    MICROSOFTAZURE = "MicrosoftAzure"
    MICROSOFTAZURESTACK = "MicrosoftAzureStack"

    def __str__(self) -> str:
        return str(self.value)
