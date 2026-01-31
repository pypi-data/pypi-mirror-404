from enum import Enum


class EEntraIdTenantUserSortingProperty(str, Enum):
    ACCOUNTENABLED = "accountEnabled"
    COMPANYNAME = "companyName"
    COUNTRY = "country"
    CREATIONTYPE = "creationType"
    DEPARTMENT = "department"
    DISPLAYNAME = "displayName"
    EMPLOYEETYPE = "employeeType"
    JOBTITLE = "jobTitle"
    LASTRESTOREPOINT = "lastRestorePoint"
    MAILADDRESS = "mailAddress"
    OBJECTID = "objectId"
    OFFICELOCATION = "officeLocation"
    USERNAME = "username"
    USERTYPE = "userType"

    def __str__(self) -> str:
        return str(self.value)
