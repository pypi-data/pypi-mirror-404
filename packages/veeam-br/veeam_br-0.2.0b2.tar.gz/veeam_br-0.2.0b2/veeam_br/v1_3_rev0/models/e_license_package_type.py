from enum import Enum


class ELicensePackageType(str, Enum):
    ADVANCED = "Advanced"
    BACKUP = "Backup"
    ESSENTIALS = "Essentials"
    FOUNDATION = "Foundation"
    INVALID = "Invalid"
    ONE = "One"
    PREMIUM = "Premium"
    STARTER = "Starter"
    SUITE = "Suite"

    def __str__(self) -> str:
        return str(self.value)
