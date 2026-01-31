from enum import Enum


class EUnstructuredDataServerType(str, Enum):
    AMAZONS3 = "AmazonS3"
    AZUREBLOB = "AzureBlob"
    FILESERVER = "FileServer"
    NASFILER = "NASFiler"
    NFSSHARE = "NFSShare"
    S3COMPATIBLE = "S3Compatible"
    SMBSHARE = "SMBShare"

    def __str__(self) -> str:
        return str(self.value)
