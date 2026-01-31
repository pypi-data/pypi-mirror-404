from enum import Enum


class ECapacityLicenseObjectType(str, Enum):
    FILESHARE = "FileShare"
    OBJECTSTORAGE = "ObjectStorage"

    def __str__(self) -> str:
        return str(self.value)
