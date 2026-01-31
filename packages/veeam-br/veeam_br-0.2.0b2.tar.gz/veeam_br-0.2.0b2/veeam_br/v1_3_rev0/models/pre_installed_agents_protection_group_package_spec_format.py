from enum import Enum


class PreInstalledAgentsProtectionGroupPackageSpecFormat(str, Enum):
    TAR = "Tar"
    ZIP = "Zip"

    def __str__(self) -> str:
        return str(self.value)
