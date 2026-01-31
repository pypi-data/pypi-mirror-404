from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_compression_level import ECompressionLevel
from ..models.e_storage_optimization import EStorageOptimization
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.backup_storage_settings_encryption_model import BackupStorageSettingsEncryptionModel


T = TypeVar("T", bound="AgentBackupStorageSettingsModel")


@_attrs_define
class AgentBackupStorageSettingsModel:
    """Backup storage settings.

    Attributes:
        compression_level (ECompressionLevel | Unset): Compression level.
        storage_optimization (EStorageOptimization | Unset): Storage optimization (depends on the target storage type
            and the size of your files).
        encryption (BackupStorageSettingsEncryptionModel | Unset): Encryption of backup files.
    """

    compression_level: ECompressionLevel | Unset = UNSET
    storage_optimization: EStorageOptimization | Unset = UNSET
    encryption: BackupStorageSettingsEncryptionModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        compression_level: str | Unset = UNSET
        if not isinstance(self.compression_level, Unset):
            compression_level = self.compression_level.value

        storage_optimization: str | Unset = UNSET
        if not isinstance(self.storage_optimization, Unset):
            storage_optimization = self.storage_optimization.value

        encryption: dict[str, Any] | Unset = UNSET
        if not isinstance(self.encryption, Unset):
            encryption = self.encryption.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if compression_level is not UNSET:
            field_dict["compressionLevel"] = compression_level
        if storage_optimization is not UNSET:
            field_dict["storageOptimization"] = storage_optimization
        if encryption is not UNSET:
            field_dict["encryption"] = encryption

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.backup_storage_settings_encryption_model import BackupStorageSettingsEncryptionModel

        d = dict(src_dict)
        _compression_level = d.pop("compressionLevel", UNSET)
        compression_level: ECompressionLevel | Unset
        if isinstance(_compression_level, Unset):
            compression_level = UNSET
        else:
            compression_level = ECompressionLevel(_compression_level)

        _storage_optimization = d.pop("storageOptimization", UNSET)
        storage_optimization: EStorageOptimization | Unset
        if isinstance(_storage_optimization, Unset):
            storage_optimization = UNSET
        else:
            storage_optimization = EStorageOptimization(_storage_optimization)

        _encryption = d.pop("encryption", UNSET)
        encryption: BackupStorageSettingsEncryptionModel | Unset
        if isinstance(_encryption, Unset):
            encryption = UNSET
        else:
            encryption = BackupStorageSettingsEncryptionModel.from_dict(_encryption)

        agent_backup_storage_settings_model = cls(
            compression_level=compression_level,
            storage_optimization=storage_optimization,
            encryption=encryption,
        )

        agent_backup_storage_settings_model.additional_properties = d
        return agent_backup_storage_settings_model

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
