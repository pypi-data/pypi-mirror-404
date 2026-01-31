from enum import Enum


class ERepositoryImmutabilityMode(str, Enum):
    REPOSITORYSETTINGS = "RepositorySettings"
    RETENTIONSETTINGS = "RetentionSettings"

    def __str__(self) -> str:
        return str(self.value)
