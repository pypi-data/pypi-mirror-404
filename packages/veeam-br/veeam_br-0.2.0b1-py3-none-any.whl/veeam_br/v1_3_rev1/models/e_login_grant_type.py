from enum import Enum


class ELoginGrantType(str, Enum):
    AUTHORIZATION_CODE = "Authorization_code"
    PASSWORD = "Password"
    REFRESH_TOKEN = "Refresh_token"
    VBR_TOKEN = "Vbr_token"

    def __str__(self) -> str:
        return str(self.value)
