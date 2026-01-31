from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_key_management_server_type import EKeyManagementServerType
from ..types import UNSET, Unset

T = TypeVar("T", bound="KeyManagementServerBaseModel")


@_attrs_define
class KeyManagementServerBaseModel:
    """
    Attributes:
        id (UUID): ID of the KMS server.
        name (str): Full DNS name or IP address of the KMS server.
        type_ (EKeyManagementServerType): KMS server type.
        description (str | Unset): KMS server description.
    """

    id: UUID
    name: str
    type_: EKeyManagementServerType
    description: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        type_ = self.type_.value

        description = self.description

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "type": type_,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        type_ = EKeyManagementServerType(d.pop("type"))

        description = d.pop("description", UNSET)

        key_management_server_base_model = cls(
            id=id,
            name=name,
            type_=type_,
            description=description,
        )

        key_management_server_base_model.additional_properties = d
        return key_management_server_base_model

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
