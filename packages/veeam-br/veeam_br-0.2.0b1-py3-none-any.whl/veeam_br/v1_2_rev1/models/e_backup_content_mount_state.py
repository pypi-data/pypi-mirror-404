from enum import Enum


class EBackupContentMountState(str, Enum):
    MOUNTED = "Mounted"
    MOUNTFAILED = "MountFailed"
    MOUNTING = "Mounting"
    UNMOUNTED = "Unmounted"
    UNMOUNTFAILED = "UnmountFailed"
    UNMOUNTING = "Unmounting"

    def __str__(self) -> str:
        return str(self.value)
