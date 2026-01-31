from enum import Enum


class EPeriodicallyKinds(str, Enum):
    DAYS = "Days"
    HOURS = "Hours"
    MINUTES = "Minutes"
    SECONDS = "Seconds"

    def __str__(self) -> str:
        return str(self.value)
