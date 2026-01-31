from enum import Enum


class EDiscoveredEntityFiltersOrderColumn(str, Enum):
    AGENTSTATUS = "AgentStatus"
    DRIVERSTATUS = "DriverStatus"
    NAME = "Name"
    OPERATINGSYSTEM = "OperatingSystem"
    STATE = "State"

    def __str__(self) -> str:
        return str(self.value)
