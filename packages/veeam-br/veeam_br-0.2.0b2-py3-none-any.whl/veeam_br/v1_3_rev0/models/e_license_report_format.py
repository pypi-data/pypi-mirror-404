from enum import Enum


class ELicenseReportFormat(str, Enum):
    HTML = "Html"
    JSON = "Json"
    PDF = "Pdf"

    def __str__(self) -> str:
        return str(self.value)
