from enum import Enum


class EAmazonS3Region(str, Enum):
    AF_SOUTH_1 = "Af-south-1"
    AP_EAST_1 = "Ap-east-1"
    AP_NORTHEAST_1 = "Ap-northeast-1"
    AP_NORTHEAST_2 = "Ap-northeast-2"
    AP_SOUTHEAST_1 = "Ap-southeast-1"
    AP_SOUTHEAST_2 = "Ap-southeast-2"
    AP_SOUTH_1 = "Ap-south-1"
    CA_CENTRAL_1 = "Ca-central-1"
    EU_CENTRAL_1 = "Eu-central-1"
    EU_NORTH_1 = "Eu-north-1"
    EU_SOUTH_1 = "Eu-south-1"
    EU_WEST_1 = "Eu-west-1"
    EU_WEST_2 = "Eu-west-2"
    EU_WEST_3 = "Eu-west-3"
    ME_SOUTH_1 = "Me-south-1"
    SA_EAST_1 = "Sa-east-1"
    UNKNOWN = "Unknown"
    US_EAST_1 = "Us-east-1"
    US_EAST_2 = "Us-east-2"
    US_WEST_1 = "Us-west-1"
    US_WEST_2 = "Us-west-2"

    def __str__(self) -> str:
        return str(self.value)
