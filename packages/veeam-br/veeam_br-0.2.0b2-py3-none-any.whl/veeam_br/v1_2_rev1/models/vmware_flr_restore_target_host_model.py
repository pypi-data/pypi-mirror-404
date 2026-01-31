from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_flr_platform_type import EFlrPlatformType

if TYPE_CHECKING:
    from ..models.inventory_object_model import InventoryObjectModel


T = TypeVar("T", bound="VmwareFlrRestoreTargetHostModel")


@_attrs_define
class VmwareFlrRestoreTargetHostModel:
    """
    Attributes:
        type_ (EFlrPlatformType): Platform type.
        vm_object (InventoryObjectModel): Inventory object properties.
    """

    type_: EFlrPlatformType
    vm_object: InventoryObjectModel
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        vm_object = self.vm_object.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "vmObject": vm_object,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.inventory_object_model import InventoryObjectModel

        d = dict(src_dict)
        type_ = EFlrPlatformType(d.pop("type"))

        vm_object = InventoryObjectModel.from_dict(d.pop("vmObject"))

        vmware_flr_restore_target_host_model = cls(
            type_=type_,
            vm_object=vm_object,
        )

        vmware_flr_restore_target_host_model.additional_properties = d
        return vmware_flr_restore_target_host_model

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
