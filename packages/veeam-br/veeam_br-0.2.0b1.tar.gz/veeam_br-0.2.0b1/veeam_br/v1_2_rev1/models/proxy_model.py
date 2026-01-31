from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_proxy_type import EProxyType

T = TypeVar("T", bound="ProxyModel")


@_attrs_define
class ProxyModel:
    """
    Attributes:
        id (UUID): ID of the backup proxy.
        name (str): Name of the backup proxy.
        description (str): Description of the backup proxy.
        type_ (EProxyType): Type of the backup proxy.
    """

    id: UUID
    name: str
    description: str
    type_: EProxyType
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        description = self.description

        type_ = self.type_.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "description": description,
                "type": type_,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        description = d.pop("description")

        type_ = EProxyType(d.pop("type"))

        proxy_model = cls(
            id=id,
            name=name,
            description=description,
            type_=type_,
        )

        proxy_model.additional_properties = d
        return proxy_model

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
