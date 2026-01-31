from enum import Enum


class ExportLogsType(str, Enum):
    ALL = "All"
    DATERANGE = "DateRange"

    def __str__(self) -> str:
        return str(self.value)
