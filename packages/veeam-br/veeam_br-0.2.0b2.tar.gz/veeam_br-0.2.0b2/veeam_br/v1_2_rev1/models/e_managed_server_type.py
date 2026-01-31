from enum import Enum


class EManagedServerType(str, Enum):
    CLOUDDIRECTORHOST = "CloudDirectorHost"
    LINUXHOST = "LinuxHost"
    VIHOST = "ViHost"
    WINDOWSHOST = "WindowsHost"

    def __str__(self) -> str:
        return str(self.value)
