from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_credentials_type import ECredentialsType
from ..types import UNSET, Unset

T = TypeVar("T", bound="ManagedServiceCredentialsSpec")


@_attrs_define
class ManagedServiceCredentialsSpec:
    """Credential settings for Group Managed Service Accounts (gMSA).

    Attributes:
        username (str): User name.
        type_ (ECredentialsType): Credentials type.
        description (str | Unset): Description of the credentials record.
        unique_id (str | Unset): Unique ID that identifies the credentials record.
    """

    username: str
    type_: ECredentialsType
    description: str | Unset = UNSET
    unique_id: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        username = self.username

        type_ = self.type_.value

        description = self.description

        unique_id = self.unique_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "username": username,
                "type": type_,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if unique_id is not UNSET:
            field_dict["uniqueId"] = unique_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        username = d.pop("username")

        type_ = ECredentialsType(d.pop("type"))

        description = d.pop("description", UNSET)

        unique_id = d.pop("uniqueId", UNSET)

        managed_service_credentials_spec = cls(
            username=username,
            type_=type_,
            description=description,
            unique_id=unique_id,
        )

        managed_service_credentials_spec.additional_properties = d
        return managed_service_credentials_spec

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
