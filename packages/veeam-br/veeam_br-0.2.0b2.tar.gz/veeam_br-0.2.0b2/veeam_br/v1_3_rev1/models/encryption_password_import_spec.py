from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="EncryptionPasswordImportSpec")


@_attrs_define
class EncryptionPasswordImportSpec:
    """Import settings for data encryption password.

    Attributes:
        password (str): Password.
        hint (str): Hint for the encryption password.
        unique_id (str | Unset): Unique ID for the encryption password.
    """

    password: str
    hint: str
    unique_id: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        password = self.password

        hint = self.hint

        unique_id = self.unique_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "password": password,
                "hint": hint,
            }
        )
        if unique_id is not UNSET:
            field_dict["uniqueId"] = unique_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        password = d.pop("password")

        hint = d.pop("hint")

        unique_id = d.pop("uniqueId", UNSET)

        encryption_password_import_spec = cls(
            password=password,
            hint=hint,
            unique_id=unique_id,
        )

        encryption_password_import_spec.additional_properties = d
        return encryption_password_import_spec

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
