from enum import Enum


class ECompressionLevel(str, Enum):
    DEDUPFRIENDLY = "DedupFriendly"
    EXTREME = "Extreme"
    HIGH = "High"
    NONE = "None"
    OPTIMAL = "Optimal"

    def __str__(self) -> str:
        return str(self.value)
