from enum import Enum


class EEntraIdTenantGroupSortingProperty(str, Enum):
    ARCHIVED = "archived"
    DESCRIPTION = "description"
    DISPLAYNAME = "displayName"
    GROUPTYPE = "groupType"
    LASTRESTOREPOINT = "lastRestorePoint"
    MAILENABLED = "mailEnabled"
    MEMBERSHIPTYPE = "membershipType"
    OBJECTID = "objectId"
    VISIBILITY = "visibility"

    def __str__(self) -> str:
        return str(self.value)
