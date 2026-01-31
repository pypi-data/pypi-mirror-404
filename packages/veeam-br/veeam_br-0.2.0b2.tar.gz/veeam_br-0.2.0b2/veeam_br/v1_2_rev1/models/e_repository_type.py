from enum import Enum


class ERepositoryType(str, Enum):
    AMAZONS3 = "AmazonS3"
    AMAZONS3GLACIER = "AmazonS3Glacier"
    AMAZONSNOWBALLEDGE = "AmazonSnowballEdge"
    AZUREARCHIVE = "AzureArchive"
    AZUREBLOB = "AzureBlob"
    AZUREDATABOX = "AzureDataBox"
    DDBOOST = "DDBoost"
    EXAGRID = "ExaGrid"
    EXTENDABLEREPOSITORY = "ExtendableRepository"
    FUJITSU = "Fujitsu"
    GOOGLECLOUD = "GoogleCloud"
    HPSTOREONCEINTEGRATION = "HPStoreOnceIntegration"
    IBMCLOUD = "IBMCloud"
    INFINIDAT = "Infinidat"
    LINUXHARDENED = "LinuxHardened"
    LINUXLOCAL = "LinuxLocal"
    NFS = "Nfs"
    QUANTUM = "Quantum"
    S3COMPATIBLE = "S3Compatible"
    SMB = "Smb"
    WASABICLOUD = "WasabiCloud"
    WINLOCAL = "WinLocal"

    def __str__(self) -> str:
        return str(self.value)
