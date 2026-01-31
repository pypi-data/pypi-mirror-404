from enum import Enum


class ECloudCredentialsFiltersOrderColumn(str, Enum):
    DESCRIPTION = "Description"
    LASTMODIFIED = "LastModified"
    NAME = "Name"
    TYPE = "Type"

    def __str__(self) -> str:
        return str(self.value)
