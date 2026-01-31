from enum import Enum


class ELinuxVolumeType(str, Enum):
    BTRFS = "BTRFS"
    DEVICE = "Device"
    LVM = "LVM"
    MOUNTPOINT = "MountPoint"

    def __str__(self) -> str:
        return str(self.value)
