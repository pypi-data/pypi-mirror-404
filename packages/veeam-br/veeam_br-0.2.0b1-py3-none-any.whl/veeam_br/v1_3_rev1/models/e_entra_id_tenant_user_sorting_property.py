from enum import Enum


class EEntraIdTenantUserSortingProperty(str, Enum):
    ACCOUNTENABLED = "AccountEnabled"
    COMPANYNAME = "CompanyName"
    COUNTRY = "Country"
    CREATIONTYPE = "CreationType"
    DEPARTMENT = "Department"
    DISPLAYNAME = "DisplayName"
    EMPLOYEETYPE = "EmployeeType"
    JOBTITLE = "JobTitle"
    LASTRESTOREPOINT = "LastRestorePoint"
    MAILADDRESS = "MailAddress"
    OBJECTID = "ObjectId"
    OFFICELOCATION = "OfficeLocation"
    USERNAME = "Username"
    USERTYPE = "UserType"

    def __str__(self) -> str:
        return str(self.value)
