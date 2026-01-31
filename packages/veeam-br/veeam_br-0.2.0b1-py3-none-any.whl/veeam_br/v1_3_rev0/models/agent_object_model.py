from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_agent_inventory_object_type import EAgentInventoryObjectType
from ..models.e_inventory_platform_type import EInventoryPlatformType
from ..types import UNSET, Unset

T = TypeVar("T", bound="AgentObjectModel")


@_attrs_define
class AgentObjectModel:
    """Agent-managed object.

    Attributes:
        platform (EInventoryPlatformType): Platform type of inventory object.
        id (UUID): ID of agent-managed object.
        name (str): Name of agent-managed object.
        type_ (EAgentInventoryObjectType): Type of agent-managed object.
        protection_group_id (UUID): Protection group ID.
        size (str | Unset): Object size.
        path (str | Unset): Path of installed agent.
        parent_object_id (UUID | Unset): Parent object ID.
    """

    platform: EInventoryPlatformType
    id: UUID
    name: str
    type_: EAgentInventoryObjectType
    protection_group_id: UUID
    size: str | Unset = UNSET
    path: str | Unset = UNSET
    parent_object_id: UUID | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        platform = self.platform.value

        id = str(self.id)

        name = self.name

        type_ = self.type_.value

        protection_group_id = str(self.protection_group_id)

        size = self.size

        path = self.path

        parent_object_id: str | Unset = UNSET
        if not isinstance(self.parent_object_id, Unset):
            parent_object_id = str(self.parent_object_id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "platform": platform,
                "id": id,
                "name": name,
                "type": type_,
                "protectionGroupId": protection_group_id,
            }
        )
        if size is not UNSET:
            field_dict["size"] = size
        if path is not UNSET:
            field_dict["path"] = path
        if parent_object_id is not UNSET:
            field_dict["parentObjectId"] = parent_object_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        platform = EInventoryPlatformType(d.pop("platform"))

        id = UUID(d.pop("id"))

        name = d.pop("name")

        type_ = EAgentInventoryObjectType(d.pop("type"))

        protection_group_id = UUID(d.pop("protectionGroupId"))

        size = d.pop("size", UNSET)

        path = d.pop("path", UNSET)

        _parent_object_id = d.pop("parentObjectId", UNSET)
        parent_object_id: UUID | Unset
        if isinstance(_parent_object_id, Unset):
            parent_object_id = UNSET
        else:
            parent_object_id = UUID(_parent_object_id)

        agent_object_model = cls(
            platform=platform,
            id=id,
            name=name,
            type_=type_,
            protection_group_id=protection_group_id,
            size=size,
            path=path,
            parent_object_id=parent_object_id,
        )

        agent_object_model.additional_properties = d
        return agent_object_model

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
