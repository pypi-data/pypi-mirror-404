from enum import Enum


class ESocketLicenseObjectType(str, Enum):
    HYPERV = "HyperV"
    UNIVERSAL = "Universal"
    UNLICENSED = "Unlicensed"
    VSPHERE = "vSphere"

    def __str__(self) -> str:
        return str(self.value)
