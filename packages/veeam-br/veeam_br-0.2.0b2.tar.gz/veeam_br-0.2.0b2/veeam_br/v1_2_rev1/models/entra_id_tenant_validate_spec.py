from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="EntraIdTenantValidateSpec")


@_attrs_define
class EntraIdTenantValidateSpec:
    """
    Attributes:
        restore_point_id (UUID): Restore point ID.
        item_ids (list[str]): Array of Microsoft Entra ID item IDs.
    """

    restore_point_id: UUID
    item_ids: list[str]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        restore_point_id = str(self.restore_point_id)

        item_ids = self.item_ids

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "restorePointId": restore_point_id,
                "itemIds": item_ids,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        restore_point_id = UUID(d.pop("restorePointId"))

        item_ids = cast(list[str], d.pop("itemIds"))

        entra_id_tenant_validate_spec = cls(
            restore_point_id=restore_point_id,
            item_ids=item_ids,
        )

        entra_id_tenant_validate_spec.additional_properties = d
        return entra_id_tenant_validate_spec

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
