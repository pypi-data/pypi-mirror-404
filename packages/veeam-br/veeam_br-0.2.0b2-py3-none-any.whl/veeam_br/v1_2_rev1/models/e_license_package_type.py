from enum import Enum


class ELicensePackageType(str, Enum):
    BACKUP = "Backup"
    ESSENTIALS = "Essentials"
    INVALID = "Invalid"
    ONE = "One"
    STARTER = "Starter"
    SUITE = "Suite"

    def __str__(self) -> str:
        return str(self.value)
