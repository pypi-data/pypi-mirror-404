from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_encryption_type import EEncryptionType
from ..types import UNSET, Unset

T = TypeVar("T", bound="BackupStorageSettingsEncryptionModel")


@_attrs_define
class BackupStorageSettingsEncryptionModel:
    """Encryption of backup files.

    Attributes:
        is_enabled (bool): If `true`, the content of backup files is encrypted.
        encryption_type (EEncryptionType | Unset): Encryption type. The property is required if data encryption is
            enabled.
        encryption_password_id (UUID | Unset): ID of the password used for encryption. The value is *null* for exported
            objects.
        encryption_password_unique_id (str | Unset): Unique ID that identifies the password.
        kms_server_id (UUID | Unset): ID of the KMS server for KMS key generation.
    """

    is_enabled: bool
    encryption_type: EEncryptionType | Unset = UNSET
    encryption_password_id: UUID | Unset = UNSET
    encryption_password_unique_id: str | Unset = UNSET
    kms_server_id: UUID | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        is_enabled = self.is_enabled

        encryption_type: str | Unset = UNSET
        if not isinstance(self.encryption_type, Unset):
            encryption_type = self.encryption_type.value

        encryption_password_id: str | Unset = UNSET
        if not isinstance(self.encryption_password_id, Unset):
            encryption_password_id = str(self.encryption_password_id)

        encryption_password_unique_id = self.encryption_password_unique_id

        kms_server_id: str | Unset = UNSET
        if not isinstance(self.kms_server_id, Unset):
            kms_server_id = str(self.kms_server_id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "isEnabled": is_enabled,
            }
        )
        if encryption_type is not UNSET:
            field_dict["encryptionType"] = encryption_type
        if encryption_password_id is not UNSET:
            field_dict["encryptionPasswordId"] = encryption_password_id
        if encryption_password_unique_id is not UNSET:
            field_dict["encryptionPasswordUniqueId"] = encryption_password_unique_id
        if kms_server_id is not UNSET:
            field_dict["kmsServerId"] = kms_server_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        is_enabled = d.pop("isEnabled")

        _encryption_type = d.pop("encryptionType", UNSET)
        encryption_type: EEncryptionType | Unset
        if isinstance(_encryption_type, Unset):
            encryption_type = UNSET
        else:
            encryption_type = EEncryptionType(_encryption_type)

        _encryption_password_id = d.pop("encryptionPasswordId", UNSET)
        encryption_password_id: UUID | Unset
        if isinstance(_encryption_password_id, Unset):
            encryption_password_id = UNSET
        else:
            encryption_password_id = UUID(_encryption_password_id)

        encryption_password_unique_id = d.pop("encryptionPasswordUniqueId", UNSET)

        _kms_server_id = d.pop("kmsServerId", UNSET)
        kms_server_id: UUID | Unset
        if isinstance(_kms_server_id, Unset):
            kms_server_id = UNSET
        else:
            kms_server_id = UUID(_kms_server_id)

        backup_storage_settings_encryption_model = cls(
            is_enabled=is_enabled,
            encryption_type=encryption_type,
            encryption_password_id=encryption_password_id,
            encryption_password_unique_id=encryption_password_unique_id,
            kms_server_id=kms_server_id,
        )

        backup_storage_settings_encryption_model.additional_properties = d
        return backup_storage_settings_encryption_model

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
