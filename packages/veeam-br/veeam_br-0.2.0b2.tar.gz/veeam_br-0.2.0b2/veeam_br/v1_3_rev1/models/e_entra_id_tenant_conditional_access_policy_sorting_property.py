from enum import Enum


class EEntraIdTenantConditionalAccessPolicySortingProperty(str, Enum):
    DISPLAYNAME = "DisplayName"
    LASTRESTOREPOINT = "LastRestorePoint"
    OBJECTID = "ObjectId"
    STATE = "State"

    def __str__(self) -> str:
        return str(self.value)
