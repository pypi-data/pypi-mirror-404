from enum import Enum


class EAzureRegionType(str, Enum):
    CHINA = "China"
    GERMANY = "Germany"
    GLOBAL = "Global"
    GOVERNMENT = "Government"

    def __str__(self) -> str:
        return str(self.value)
