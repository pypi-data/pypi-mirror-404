from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

T = TypeVar("T", bound="EntraIdTenantProductionItemModel")


@_attrs_define
class EntraIdTenantProductionItemModel:
    """
    Attributes:
        item_id (str): Item ID.
        display_name (str): Item display name.
        restore_point_id (UUID): Restore point ID.
        restore_point_date (datetime.datetime): Date and time when the restore point was created.
    """

    item_id: str
    display_name: str
    restore_point_id: UUID
    restore_point_date: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        item_id = self.item_id

        display_name = self.display_name

        restore_point_id = str(self.restore_point_id)

        restore_point_date = self.restore_point_date.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "itemId": item_id,
                "displayName": display_name,
                "restorePointId": restore_point_id,
                "restorePointDate": restore_point_date,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        item_id = d.pop("itemId")

        display_name = d.pop("displayName")

        restore_point_id = UUID(d.pop("restorePointId"))

        restore_point_date = isoparse(d.pop("restorePointDate"))

        entra_id_tenant_production_item_model = cls(
            item_id=item_id,
            display_name=display_name,
            restore_point_id=restore_point_id,
            restore_point_date=restore_point_date,
        )

        entra_id_tenant_production_item_model.additional_properties = d
        return entra_id_tenant_production_item_model

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
