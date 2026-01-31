from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="EntraIdResource")


@_attrs_define
class EntraIdResource:
    """Resource consumption.

    Attributes:
        cpu_resource (int): CPU consumption for restore.
        ram_resource (int): RAM consumption.
        item_resource (int): Total number of tenant items.
        cpu_backup_resource (int): CPU consumption for backup.
    """

    cpu_resource: int
    ram_resource: int
    item_resource: int
    cpu_backup_resource: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        cpu_resource = self.cpu_resource

        ram_resource = self.ram_resource

        item_resource = self.item_resource

        cpu_backup_resource = self.cpu_backup_resource

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "cpuResource": cpu_resource,
                "ramResource": ram_resource,
                "itemResource": item_resource,
                "cpuBackupResource": cpu_backup_resource,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        cpu_resource = d.pop("cpuResource")

        ram_resource = d.pop("ramResource")

        item_resource = d.pop("itemResource")

        cpu_backup_resource = d.pop("cpuBackupResource")

        entra_id_resource = cls(
            cpu_resource=cpu_resource,
            ram_resource=ram_resource,
            item_resource=item_resource,
            cpu_backup_resource=cpu_backup_resource,
        )

        entra_id_resource.additional_properties = d
        return entra_id_resource

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
