from enum import Enum


class EInstanceWorkloadsFiltersOrderColumn(str, Enum):
    HOSTNAME = "HostName"
    INSTANCEID = "InstanceId"
    NAME = "Name"
    TYPE = "Type"
    USEDINSTANCESNUMBER = "UsedInstancesNumber"

    def __str__(self) -> str:
        return str(self.value)
