from enum import Enum


class EDiskInfoType(str, Enum):
    ENDPOINT = "EndPoint"
    HV = "Hv"
    HVRAWDISKFILE = "HvRawDiskFile"
    SIMPLE = "Simple"
    UNKNOWN = "Unknown"
    VI = "Vi"

    def __str__(self) -> str:
        return str(self.value)
