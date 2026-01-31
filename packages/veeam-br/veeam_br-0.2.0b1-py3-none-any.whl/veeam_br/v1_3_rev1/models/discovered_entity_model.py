from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_discovered_entity_type import EDiscoveredEntityType
from ..types import UNSET, Unset

T = TypeVar("T", bound="DiscoveredEntityModel")


@_attrs_define
class DiscoveredEntityModel:
    """Discovered entity.

    Attributes:
        id (UUID): Discovered entity ID.
        name (str): Discovered entity name.
        parent_id (UUID): Parent ID of the discovered entity.
        protection_group_id (UUID): Protection group ID.
        type_ (EDiscoveredEntityType | Unset): Discovered entity type.
    """

    id: UUID
    name: str
    parent_id: UUID
    protection_group_id: UUID
    type_: EDiscoveredEntityType | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        parent_id = str(self.parent_id)

        protection_group_id = str(self.protection_group_id)

        type_: str | Unset = UNSET
        if not isinstance(self.type_, Unset):
            type_ = self.type_.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "parentId": parent_id,
                "protectionGroupId": protection_group_id,
            }
        )
        if type_ is not UNSET:
            field_dict["type"] = type_

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        parent_id = UUID(d.pop("parentId"))

        protection_group_id = UUID(d.pop("protectionGroupId"))

        _type_ = d.pop("type", UNSET)
        type_: EDiscoveredEntityType | Unset
        if isinstance(_type_, Unset):
            type_ = UNSET
        else:
            type_ = EDiscoveredEntityType(_type_)

        discovered_entity_model = cls(
            id=id,
            name=name,
            parent_id=parent_id,
            protection_group_id=protection_group_id,
            type_=type_,
        )

        discovered_entity_model.additional_properties = d
        return discovered_entity_model

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
