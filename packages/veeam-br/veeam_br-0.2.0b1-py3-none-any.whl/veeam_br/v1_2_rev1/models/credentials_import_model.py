from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CredentialsImportModel")


@_attrs_define
class CredentialsImportModel:
    """Credentials used for connection.

    Attributes:
        credentials_name (str): User name, account name or access key.
        credentials_tag (str | Unset): Tag used to identify the credentials record.
    """

    credentials_name: str
    credentials_tag: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        credentials_name = self.credentials_name

        credentials_tag = self.credentials_tag

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "credentialsName": credentials_name,
            }
        )
        if credentials_tag is not UNSET:
            field_dict["credentialsTag"] = credentials_tag

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        credentials_name = d.pop("credentialsName")

        credentials_tag = d.pop("credentialsTag", UNSET)

        credentials_import_model = cls(
            credentials_name=credentials_name,
            credentials_tag=credentials_tag,
        )

        credentials_import_model.additional_properties = d
        return credentials_import_model

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
