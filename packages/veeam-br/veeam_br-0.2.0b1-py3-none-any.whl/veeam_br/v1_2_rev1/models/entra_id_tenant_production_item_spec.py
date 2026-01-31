from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="EntraIdTenantProductionItemSpec")


@_attrs_define
class EntraIdTenantProductionItemSpec:
    """
    Attributes:
        item_id (str): Item ID.
        restore_point_id (UUID): Restore point ID.
    """

    item_id: str
    restore_point_id: UUID
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        item_id = self.item_id

        restore_point_id = str(self.restore_point_id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "itemId": item_id,
                "restorePointId": restore_point_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        item_id = d.pop("itemId")

        restore_point_id = UUID(d.pop("restorePointId"))

        entra_id_tenant_production_item_spec = cls(
            item_id=item_id,
            restore_point_id=restore_point_id,
        )

        entra_id_tenant_production_item_spec.additional_properties = d
        return entra_id_tenant_production_item_spec

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
