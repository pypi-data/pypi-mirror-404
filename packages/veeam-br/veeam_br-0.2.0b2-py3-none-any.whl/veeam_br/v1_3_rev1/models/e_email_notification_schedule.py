from enum import Enum


class EEmailNotificationSchedule(str, Enum):
    DAILY = "Daily"
    IMMEDIATE = "Immediate"

    def __str__(self) -> str:
        return str(self.value)
