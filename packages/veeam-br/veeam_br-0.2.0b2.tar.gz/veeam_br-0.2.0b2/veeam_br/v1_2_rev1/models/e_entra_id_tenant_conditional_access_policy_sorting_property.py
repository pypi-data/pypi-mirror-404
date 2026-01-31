from enum import Enum


class EEntraIdTenantConditionalAccessPolicySortingProperty(str, Enum):
    DISPLAYNAME = "displayName"
    LASTRESTOREPOINT = "lastRestorePoint"
    OBJECTID = "objectId"
    STATE = "state"

    def __str__(self) -> str:
        return str(self.value)
