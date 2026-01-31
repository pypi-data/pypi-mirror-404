from enum import Enum


class ELinuxPackageFiltersOrderColumn(str, Enum):
    DISTRIBUTIONNAME = "DistributionName"
    NAME = "Name"

    def __str__(self) -> str:
        return str(self.value)
