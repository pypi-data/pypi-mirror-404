from enum import Enum


class EEmailNotificationType(str, Enum):
    USECUSTOMNOTIFICATIONSETTINGS = "UseCustomNotificationSettings"
    USEGLOBALNOTIFICATIONSETTINGS = "UseGlobalNotificationSettings"

    def __str__(self) -> str:
        return str(self.value)
