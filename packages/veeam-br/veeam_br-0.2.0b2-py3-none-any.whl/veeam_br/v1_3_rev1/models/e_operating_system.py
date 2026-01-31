from enum import Enum


class EOperatingSystem(str, Enum):
    AZURESTACKHCI = "AzureStackHCI"
    LINUX = "Linux"
    UNKNOWN = "Unknown"
    WINDOWS10 = "Windows10"
    WINDOWS11 = "Windows11"
    WINDOWS2003 = "Windows2003"
    WINDOWS2008 = "Windows2008"
    WINDOWS7 = "Windows7"
    WINDOWS8 = "Windows8"
    WINDOWS81 = "Windows81"
    WINDOWSSERVER2008R2 = "WindowsServer2008R2"
    WINDOWSSERVER2012 = "WindowsServer2012"
    WINDOWSSERVER2012R2 = "WindowsServer2012R2"
    WINDOWSSERVER2016 = "WindowsServer2016"
    WINDOWSSERVER2016NANO = "WindowsServer2016Nano"
    WINDOWSSERVER2019 = "WindowsServer2019"
    WINDOWSSERVER2022 = "WindowsServer2022"
    WINDOWSSERVER2025 = "WindowsServer2025"
    WINDOWSSERVERNEXT = "WindowsServerNext"
    WINDOWSVISTA = "WindowsVista"
    WINDOWSXP = "WindowsXP"

    def __str__(self) -> str:
        return str(self.value)
