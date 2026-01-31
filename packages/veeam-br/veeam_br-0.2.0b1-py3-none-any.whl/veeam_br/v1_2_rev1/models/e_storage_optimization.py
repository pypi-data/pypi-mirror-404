from enum import Enum


class EStorageOptimization(str, Enum):
    LANTARGET = "LANTarget"
    LOCALTARGET = "LocalTarget"
    LOCALTARGETLARGE = "LocalTargetLarge"
    LOCALTARGETLARGE4096 = "LocalTargetLarge4096"
    LOCALTARGETLARGE8192 = "LocalTargetLarge8192"
    WANTARGET = "WANTarget"

    def __str__(self) -> str:
        return str(self.value)
