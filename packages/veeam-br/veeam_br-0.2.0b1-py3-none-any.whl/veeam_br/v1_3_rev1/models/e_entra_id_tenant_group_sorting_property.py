from enum import Enum


class EEntraIdTenantGroupSortingProperty(str, Enum):
    ARCHIVED = "Archived"
    DESCRIPTION = "Description"
    DISPLAYNAME = "DisplayName"
    GROUPTYPE = "GroupType"
    LASTRESTOREPOINT = "LastRestorePoint"
    MAILENABLED = "MailEnabled"
    MEMBERSHIPTYPE = "MembershipType"
    OBJECTID = "ObjectId"
    VISIBILITY = "Visibility"

    def __str__(self) -> str:
        return str(self.value)
