from enum import Enum


class ECredentialsFiltersOrderColumn(str, Enum):
    DESCRIPTION = "Description"
    USERNAME = "Username"

    def __str__(self) -> str:
        return str(self.value)
