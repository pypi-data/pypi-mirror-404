from enum import Enum


class ECredentialsFiltersOrderColumn(str, Enum):
    CREATIONTIME = "CreationTime"
    DESCRIPTION = "Description"
    TYPE = "Type"
    USERNAME = "Username"

    def __str__(self) -> str:
        return str(self.value)
