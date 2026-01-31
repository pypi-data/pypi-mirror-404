from enum import Enum


class EBackupEncryptionState(str, Enum):
    DECRYPTED = "Decrypted"
    ENCRYPTED = "Encrypted"
    UNENCRYPTED = "Unencrypted"

    def __str__(self) -> str:
        return str(self.value)
