from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_inventory_platform_type import EInventoryPlatformType
from ..types import UNSET, Unset

T = TypeVar("T", bound="InventoryObjectModel")


@_attrs_define
class InventoryObjectModel:
    """Inventory object properties.

    Attributes:
        platform (EInventoryPlatformType): Platform type of inventory object.
        size (str | Unset): Object size.
    """

    platform: EInventoryPlatformType
    size: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        platform = self.platform.value

        size = self.size

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "platform": platform,
            }
        )
        if size is not UNSET:
            field_dict["size"] = size

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        platform = EInventoryPlatformType(d.pop("platform"))

        size = d.pop("size", UNSET)

        inventory_object_model = cls(
            platform=platform,
            size=size,
        )

        inventory_object_model.additional_properties = d
        return inventory_object_model

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
