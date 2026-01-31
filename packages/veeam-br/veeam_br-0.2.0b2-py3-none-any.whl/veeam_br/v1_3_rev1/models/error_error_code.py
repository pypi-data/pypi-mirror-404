from enum import Enum


class ErrorErrorCode(str, Enum):
    ACCESSDENIED = "AccessDenied"
    EXPIREDTOKEN = "ExpiredToken"
    INVALIDTOKEN = "InvalidToken"
    INVALIDURI = "InvalidURI"
    METHODNOTALLOWED = "MethodNotAllowed"
    NOTFOUND = "NotFound"
    NOTIMPLEMENTED = "NotImplemented"
    SERVICEUNAVAILABLE = "ServiceUnavailable"
    UNEXPECTEDCONTENT = "UnexpectedContent"
    UNKNOWNERROR = "UnknownError"

    def __str__(self) -> str:
        return str(self.value)
