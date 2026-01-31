from enum import Enum


class EAuthorizationEventState(str, Enum):
    APPROVED = "Approved"
    EXPIRED = "Expired"
    INFO = "Info"
    PENDING = "Pending"
    REJECTED = "Rejected"

    def __str__(self) -> str:
        return str(self.value)
