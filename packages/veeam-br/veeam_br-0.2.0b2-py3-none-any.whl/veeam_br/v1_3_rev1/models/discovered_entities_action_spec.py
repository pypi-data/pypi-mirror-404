from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="DiscoveredEntitiesActionSpec")


@_attrs_define
class DiscoveredEntitiesActionSpec:
    """Settings for discovered entities.

    Attributes:
        entity_ids (list[UUID]): Array of discovered entity IDs to process. To get the discovered entity IDs, run the
            [Get Discovered Entities](Agents#operation/GetDiscoveredEntities) request.
    """

    entity_ids: list[UUID]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        entity_ids = []
        for entity_ids_item_data in self.entity_ids:
            entity_ids_item = str(entity_ids_item_data)
            entity_ids.append(entity_ids_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "entityIds": entity_ids,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        entity_ids = []
        _entity_ids = d.pop("entityIds")
        for entity_ids_item_data in _entity_ids:
            entity_ids_item = UUID(entity_ids_item_data)

            entity_ids.append(entity_ids_item)

        discovered_entities_action_spec = cls(
            entity_ids=entity_ids,
        )

        discovered_entities_action_spec.additional_properties = d
        return discovered_entities_action_spec

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
