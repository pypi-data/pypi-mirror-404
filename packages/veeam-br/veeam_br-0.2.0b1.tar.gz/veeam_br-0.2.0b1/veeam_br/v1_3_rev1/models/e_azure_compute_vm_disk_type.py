from enum import Enum


class EAzureComputeVMDiskType(str, Enum):
    PREMIUMSSD = "PremiumSSD"
    STANDARDHDD = "StandardHDD"
    STANDARDSSD = "StandardSSD"

    def __str__(self) -> str:
        return str(self.value)
