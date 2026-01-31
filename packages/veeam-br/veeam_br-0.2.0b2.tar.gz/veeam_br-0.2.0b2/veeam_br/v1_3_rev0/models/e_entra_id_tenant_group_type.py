from enum import Enum


class EEntraIdTenantGroupType(str, Enum):
    DISTRIBUTIONGROUP = "DistributionGroup"
    MAILENABLEDSECURITYGROUP = "MailEnabledSecurityGroup"
    MICROSOFT365GROUP = "Microsoft365Group"
    SECURITYGROUP = "SecurityGroup"

    def __str__(self) -> str:
        return str(self.value)
