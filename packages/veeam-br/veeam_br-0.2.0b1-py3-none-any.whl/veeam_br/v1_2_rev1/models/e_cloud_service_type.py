from enum import Enum


class ECloudServiceType(str, Enum):
    AMAZONEC2 = "AmazonEC2"
    AMAZONS3 = "AmazonS3"
    AMAZONSNOWBALLEDGE = "AmazonSnowballEdge"
    AZUREBLOB = "AzureBlob"
    AZURECOMPUTE = "AzureCompute"
    AZUREDATABOX = "AzureDataBox"
    GOOGLECLOUD = "GoogleCloud"
    IBMCLOUD = "IBMCloud"
    S3COMPATIBLE = "S3Compatible"
    WASABICLOUD = "WasabiCloud"

    def __str__(self) -> str:
        return str(self.value)
