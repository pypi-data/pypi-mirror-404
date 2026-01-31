from enum import Enum


class EUnstructuredDataInstantRecoveryMountState(str, Enum):
    PUBLISHED = "Published"
    PUBLISHFAILED = "PublishFailed"
    PUBLISHING = "Publishing"
    UNPUBLISHED = "Unpublished"
    UNPUBLISHFAILED = "UnpublishFailed"
    UNPUBLISHING = "Unpublishing"

    def __str__(self) -> str:
        return str(self.value)
