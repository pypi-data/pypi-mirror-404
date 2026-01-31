from enum import Enum


class EJobDataTransferModel(str, Enum):
    DIRECT = "Direct"
    WANACCELERATOR = "WANAccelerator"

    def __str__(self) -> str:
        return str(self.value)
