from enum import Enum


class ELoginGrantType(str, Enum):
    AUTHORIZATION_CODE = "authorization_code"
    PASSWORD = "password"
    REFRESH_TOKEN = "refresh_token"
    VBR_TOKEN = "vbr_token"

    def __str__(self) -> str:
        return str(self.value)
