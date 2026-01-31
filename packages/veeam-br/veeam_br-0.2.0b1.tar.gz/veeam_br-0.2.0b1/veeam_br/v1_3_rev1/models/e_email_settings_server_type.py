from enum import Enum


class EEmailSettingsServerType(str, Enum):
    GMAIL = "Gmail"
    MS365 = "MS365"
    SMTP = "SMTP"

    def __str__(self) -> str:
        return str(self.value)
