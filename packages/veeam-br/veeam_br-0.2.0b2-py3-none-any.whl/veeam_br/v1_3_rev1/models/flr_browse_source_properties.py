from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="FlrBrowseSourceProperties")


@_attrs_define
class FlrBrowseSourceProperties:
    """Restore point settings.

    Attributes:
        machine_name (str): Name of a virtual or physical machine.
        restore_point_name (str): Display name of the restore point (equals to the machine name).
    """

    machine_name: str
    restore_point_name: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        machine_name = self.machine_name

        restore_point_name = self.restore_point_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "machineName": machine_name,
                "restorePointName": restore_point_name,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        machine_name = d.pop("machineName")

        restore_point_name = d.pop("restorePointName")

        flr_browse_source_properties = cls(
            machine_name=machine_name,
            restore_point_name=restore_point_name,
        )

        flr_browse_source_properties.additional_properties = d
        return flr_browse_source_properties

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
