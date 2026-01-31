from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_disk_info_process_state import EDiskInfoProcessState
from ..models.e_disk_info_type import EDiskInfoType

T = TypeVar("T", bound="ObjectRestorePointDiskModel")


@_attrs_define
class ObjectRestorePointDiskModel:
    """
    Attributes:
        uid (str): ID of the disk.
        type_ (EDiskInfoType): Type of the disk.
        name (str): Name of the disk.
        capacity (int): Capacity of the disk.
        state (EDiskInfoProcessState): Process state of the disk.
    """

    uid: str
    type_: EDiskInfoType
    name: str
    capacity: int
    state: EDiskInfoProcessState
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        uid = self.uid

        type_ = self.type_.value

        name = self.name

        capacity = self.capacity

        state = self.state.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "uid": uid,
                "type": type_,
                "name": name,
                "capacity": capacity,
                "state": state,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        uid = d.pop("uid")

        type_ = EDiskInfoType(d.pop("type"))

        name = d.pop("name")

        capacity = d.pop("capacity")

        state = EDiskInfoProcessState(d.pop("state"))

        object_restore_point_disk_model = cls(
            uid=uid,
            type_=type_,
            name=name,
            capacity=capacity,
            state=state,
        )

        object_restore_point_disk_model.additional_properties = d
        return object_restore_point_disk_model

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
