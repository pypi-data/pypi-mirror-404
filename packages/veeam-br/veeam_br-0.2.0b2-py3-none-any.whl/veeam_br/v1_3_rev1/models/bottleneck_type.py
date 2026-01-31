from enum import Enum


class BottleneckType(str, Enum):
    CPU = "Cpu"
    CPUBACKUP = "CpuBackup"
    HUGETENANT = "HugeTenant"
    NOISSUES = "NoIssues"
    RAM = "Ram"

    def __str__(self) -> str:
        return str(self.value)
