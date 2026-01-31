from enum import Enum


class EAmazonRegionType(str, Enum):
    CHINA = "China"
    GLOBAL = "Global"
    GOVERNMENT = "Government"

    def __str__(self) -> str:
        return str(self.value)
