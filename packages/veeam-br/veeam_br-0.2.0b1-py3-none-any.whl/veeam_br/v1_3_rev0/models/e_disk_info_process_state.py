from enum import Enum


class EDiskInfoProcessState(str, Enum):
    INPROCESSING = "InProcessing"
    NOTPROCESSED = "NotProcessed"
    PARTIALLYPROCESSED = "PartiallyProcessed"
    PROCESSED = "Processed"

    def __str__(self) -> str:
        return str(self.value)
