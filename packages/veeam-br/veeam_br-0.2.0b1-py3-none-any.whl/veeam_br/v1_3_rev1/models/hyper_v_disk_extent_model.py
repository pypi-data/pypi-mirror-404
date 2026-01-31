from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="HyperVDiskExtentModel")


@_attrs_define
class HyperVDiskExtentModel:
    """Disk extent of Microsoft Hyper-V host.

    Attributes:
        uid (str): ID of the disk.
        name (str): Name of the disk.
        path (str): Path to the disk extent on the Microsoft Hyper-V host.
        size (int): Size of the disk in bytes.
    """

    uid: str
    name: str
    path: str
    size: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        uid = self.uid

        name = self.name

        path = self.path

        size = self.size

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "uid": uid,
                "name": name,
                "path": path,
                "size": size,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        uid = d.pop("uid")

        name = d.pop("name")

        path = d.pop("path")

        size = d.pop("size")

        hyper_v_disk_extent_model = cls(
            uid=uid,
            name=name,
            path=path,
            size=size,
        )

        hyper_v_disk_extent_model.additional_properties = d
        return hyper_v_disk_extent_model

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
