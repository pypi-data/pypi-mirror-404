from enum import Enum


class BottleneckType(str, Enum):
    CPU = "cpu"
    CPUBACKUP = "cpuBackup"
    HUGETENANT = "hugeTenant"
    NOISSUES = "noIssues"
    RAM = "ram"

    def __str__(self) -> str:
        return str(self.value)
