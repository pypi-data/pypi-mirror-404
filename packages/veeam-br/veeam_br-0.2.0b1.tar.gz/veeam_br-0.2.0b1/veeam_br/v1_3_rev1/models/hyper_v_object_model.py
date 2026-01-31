from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_hyper_v_inventory_type import EHyperVInventoryType
from ..models.e_inventory_platform_type import EInventoryPlatformType
from ..types import UNSET, Unset

T = TypeVar("T", bound="HyperVObjectModel")


@_attrs_define
class HyperVObjectModel:
    """Microsoft Hyper-V object.

    Attributes:
        platform (EInventoryPlatformType): Platform type of inventory object.
        host_name (str): Name of the Microsoft Hyper-V server that hosts the object.
        name (str): Name of the Microsoft Hyper-V object.
        type_ (EHyperVInventoryType): Type of Microsoft Hyper-V object.
        object_id (str): ID of the Microsoft Hyper-V object.
        size (str | Unset): Object size.
        urn (str | Unset): Uniform Resource Name (URN) of the object.
        parent_object_id (str | Unset): Parent object ID.
    """

    platform: EInventoryPlatformType
    host_name: str
    name: str
    type_: EHyperVInventoryType
    object_id: str
    size: str | Unset = UNSET
    urn: str | Unset = UNSET
    parent_object_id: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        platform = self.platform.value

        host_name = self.host_name

        name = self.name

        type_ = self.type_.value

        object_id = self.object_id

        size = self.size

        urn = self.urn

        parent_object_id = self.parent_object_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "platform": platform,
                "hostName": host_name,
                "name": name,
                "type": type_,
                "objectId": object_id,
            }
        )
        if size is not UNSET:
            field_dict["size"] = size
        if urn is not UNSET:
            field_dict["urn"] = urn
        if parent_object_id is not UNSET:
            field_dict["parentObjectId"] = parent_object_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        platform = EInventoryPlatformType(d.pop("platform"))

        host_name = d.pop("hostName")

        name = d.pop("name")

        type_ = EHyperVInventoryType(d.pop("type"))

        object_id = d.pop("objectId")

        size = d.pop("size", UNSET)

        urn = d.pop("urn", UNSET)

        parent_object_id = d.pop("parentObjectId", UNSET)

        hyper_v_object_model = cls(
            platform=platform,
            host_name=host_name,
            name=name,
            type_=type_,
            object_id=object_id,
            size=size,
            urn=urn,
            parent_object_id=parent_object_id,
        )

        hyper_v_object_model.additional_properties = d
        return hyper_v_object_model

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
