from enum import Enum


class EPublishBackupContentModeType(str, Enum):
    FUSELINUXMOUNT = "FUSELinuxMount"
    ISCSITARGET = "ISCSITarget"
    ISCSIWINDOWSMOUNT = "ISCSIWindowsMount"

    def __str__(self) -> str:
        return str(self.value)
