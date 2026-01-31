from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="ConfigBackupEncryptionModel")


@_attrs_define
class ConfigBackupEncryptionModel:
    """Encryption settings.

    Attributes:
        is_enabled (bool): If `true`, backup encryption is enabled.
        password_id (UUID): ID of the password used for encryption.
    """

    is_enabled: bool
    password_id: UUID
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        is_enabled = self.is_enabled

        password_id = str(self.password_id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "isEnabled": is_enabled,
                "passwordId": password_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        is_enabled = d.pop("isEnabled")

        password_id = UUID(d.pop("passwordId"))

        config_backup_encryption_model = cls(
            is_enabled=is_enabled,
            password_id=password_id,
        )

        config_backup_encryption_model.additional_properties = d
        return config_backup_encryption_model

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
