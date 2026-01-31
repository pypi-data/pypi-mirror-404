from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_disk_info_process_state import EDiskInfoProcessState
from ..models.e_disk_info_type import EDiskInfoType
from ..models.e_platform_type import EPlatformType

if TYPE_CHECKING:
    from ..models.hyper_v_disk_extent_model import HyperVDiskExtentModel


T = TypeVar("T", bound="HyperVObjectRestorePointDiskModel")


@_attrs_define
class HyperVObjectRestorePointDiskModel:
    """Microsoft Hyper-V disk.

    Attributes:
        platform (EPlatformType): Platform type.
        uid (str): ID of the disk.
        type_ (EDiskInfoType): Type of the disk.
        name (str): Name of the disk.
        capacity (int): Capacity of the disk.
        state (EDiskInfoProcessState): Process state of the disk.
        disk_extents (list[HyperVDiskExtentModel]): Array of disk extents.
    """

    platform: EPlatformType
    uid: str
    type_: EDiskInfoType
    name: str
    capacity: int
    state: EDiskInfoProcessState
    disk_extents: list[HyperVDiskExtentModel]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        platform = self.platform.value

        uid = self.uid

        type_ = self.type_.value

        name = self.name

        capacity = self.capacity

        state = self.state.value

        disk_extents = []
        for disk_extents_item_data in self.disk_extents:
            disk_extents_item = disk_extents_item_data.to_dict()
            disk_extents.append(disk_extents_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "platform": platform,
                "uid": uid,
                "type": type_,
                "name": name,
                "capacity": capacity,
                "state": state,
                "diskExtents": disk_extents,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.hyper_v_disk_extent_model import HyperVDiskExtentModel

        d = dict(src_dict)
        platform = EPlatformType(d.pop("platform"))

        uid = d.pop("uid")

        type_ = EDiskInfoType(d.pop("type"))

        name = d.pop("name")

        capacity = d.pop("capacity")

        state = EDiskInfoProcessState(d.pop("state"))

        disk_extents = []
        _disk_extents = d.pop("diskExtents")
        for disk_extents_item_data in _disk_extents:
            disk_extents_item = HyperVDiskExtentModel.from_dict(disk_extents_item_data)

            disk_extents.append(disk_extents_item)

        hyper_v_object_restore_point_disk_model = cls(
            platform=platform,
            uid=uid,
            type_=type_,
            name=name,
            capacity=capacity,
            state=state,
            disk_extents=disk_extents,
        )

        hyper_v_object_restore_point_disk_model.additional_properties = d
        return hyper_v_object_restore_point_disk_model

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
