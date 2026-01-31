from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_credentials_type import ECredentialsType
from ..types import UNSET, Unset

T = TypeVar("T", bound="CredentialsSpec")


@_attrs_define
class CredentialsSpec:
    """
    Attributes:
        username (str): User name.
        type_ (ECredentialsType): Credentials type.
        password (str | Unset): Password.
        description (str | Unset): Description of the credentials record.
    """

    username: str
    type_: ECredentialsType
    password: str | Unset = UNSET
    description: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        username = self.username

        type_ = self.type_.value

        password = self.password

        description = self.description

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "username": username,
                "type": type_,
            }
        )
        if password is not UNSET:
            field_dict["password"] = password
        if description is not UNSET:
            field_dict["description"] = description

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        username = d.pop("username")

        type_ = ECredentialsType(d.pop("type"))

        password = d.pop("password", UNSET)

        description = d.pop("description", UNSET)

        credentials_spec = cls(
            username=username,
            type_=type_,
            password=password,
            description=description,
        )

        credentials_spec.additional_properties = d
        return credentials_spec

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
