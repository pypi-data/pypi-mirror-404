from enum import Enum


class ESessionBottleneckType(str, Enum):
    NETWORK = "Network"
    NONE = "None"
    NOTDEFINED = "NotDefined"
    PROXY = "Proxy"
    SOURCE = "Source"
    SOURCENETWORK = "SourceNetwork"
    SOURCEPROXY = "SourceProxy"
    SOURCEWAN = "SourceWan"
    TARGET = "Target"
    TARGETDISK = "TargetDisk"
    TARGETNETWORK = "TargetNetwork"
    TARGETPROXY = "TargetProxy"
    TARGETWAN = "TargetWan"
    THROTTLING = "Throttling"

    def __str__(self) -> str:
        return str(self.value)
