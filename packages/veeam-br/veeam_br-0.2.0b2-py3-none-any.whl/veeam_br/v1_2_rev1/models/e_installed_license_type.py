from enum import Enum


class EInstalledLicenseType(str, Enum):
    EMPTY = "Empty"
    EVALUATION = "Evaluation"
    FREE = "Free"
    NFR = "NFR"
    PERPETUAL = "Perpetual"
    PROMO = "Promo"
    RENTAL = "Rental"
    SUBSCRIPTION = "Subscription"

    def __str__(self) -> str:
        return str(self.value)
