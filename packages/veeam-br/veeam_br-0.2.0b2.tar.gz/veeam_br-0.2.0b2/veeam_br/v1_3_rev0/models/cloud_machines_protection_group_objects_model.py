from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_cloud_machines_object_type import ECloudMachinesObjectType
from ..types import UNSET, Unset

T = TypeVar("T", bound="CloudMachinesProtectionGroupObjectsModel")


@_attrs_define
class CloudMachinesProtectionGroupObjectsModel:
    """Cloud object added to the protection group.

    Attributes:
        name (str | Unset): Cloud object name.
        object_id (str | Unset): Cloud object ID.
        type_ (ECloudMachinesObjectType | Unset): Cloud object type.
    """

    name: str | Unset = UNSET
    object_id: str | Unset = UNSET
    type_: ECloudMachinesObjectType | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        object_id = self.object_id

        type_: str | Unset = UNSET
        if not isinstance(self.type_, Unset):
            type_ = self.type_.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if object_id is not UNSET:
            field_dict["objectId"] = object_id
        if type_ is not UNSET:
            field_dict["type"] = type_

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name", UNSET)

        object_id = d.pop("objectId", UNSET)

        _type_ = d.pop("type", UNSET)
        type_: ECloudMachinesObjectType | Unset
        if isinstance(_type_, Unset):
            type_ = UNSET
        else:
            type_ = ECloudMachinesObjectType(_type_)

        cloud_machines_protection_group_objects_model = cls(
            name=name,
            object_id=object_id,
            type_=type_,
        )

        cloud_machines_protection_group_objects_model.additional_properties = d
        return cloud_machines_protection_group_objects_model

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
