from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.encryption_password_import_spec import EncryptionPasswordImportSpec


T = TypeVar("T", bound="EncryptionPasswordImportSpecCollection")


@_attrs_define
class EncryptionPasswordImportSpecCollection:
    """Collection of import settings for data encryption passwords.

    Attributes:
        encryption_passwords (list[EncryptionPasswordImportSpec] | Unset): Array of encryption passwords.
    """

    encryption_passwords: list[EncryptionPasswordImportSpec] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        encryption_passwords: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.encryption_passwords, Unset):
            encryption_passwords = []
            for encryption_passwords_item_data in self.encryption_passwords:
                encryption_passwords_item = encryption_passwords_item_data.to_dict()
                encryption_passwords.append(encryption_passwords_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if encryption_passwords is not UNSET:
            field_dict["encryptionPasswords"] = encryption_passwords

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.encryption_password_import_spec import EncryptionPasswordImportSpec

        d = dict(src_dict)
        _encryption_passwords = d.pop("encryptionPasswords", UNSET)
        encryption_passwords: list[EncryptionPasswordImportSpec] | Unset = UNSET
        if _encryption_passwords is not UNSET:
            encryption_passwords = []
            for encryption_passwords_item_data in _encryption_passwords:
                encryption_passwords_item = EncryptionPasswordImportSpec.from_dict(encryption_passwords_item_data)

                encryption_passwords.append(encryption_passwords_item)

        encryption_password_import_spec_collection = cls(
            encryption_passwords=encryption_passwords,
        )

        encryption_password_import_spec_collection.additional_properties = d
        return encryption_password_import_spec_collection

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
