from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.inventory_object_model import InventoryObjectModel


T = TypeVar("T", bound="VmwareFailoverPlanVirtualMachineModel")


@_attrs_define
class VmwareFailoverPlanVirtualMachineModel:
    """VM added to the failover plan.

    Attributes:
        vm_object (InventoryObjectModel | Unset): Inventory object properties.
        boot_delay_sec (int | Unset): Delay time for the VM to boot, in seconds.
    """

    vm_object: InventoryObjectModel | Unset = UNSET
    boot_delay_sec: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        vm_object: dict[str, Any] | Unset = UNSET
        if not isinstance(self.vm_object, Unset):
            vm_object = self.vm_object.to_dict()

        boot_delay_sec = self.boot_delay_sec

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if vm_object is not UNSET:
            field_dict["vmObject"] = vm_object
        if boot_delay_sec is not UNSET:
            field_dict["bootDelaySec"] = boot_delay_sec

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.inventory_object_model import InventoryObjectModel

        d = dict(src_dict)
        _vm_object = d.pop("vmObject", UNSET)
        vm_object: InventoryObjectModel | Unset
        if isinstance(_vm_object, Unset):
            vm_object = UNSET
        else:
            vm_object = InventoryObjectModel.from_dict(_vm_object)

        boot_delay_sec = d.pop("bootDelaySec", UNSET)

        vmware_failover_plan_virtual_machine_model = cls(
            vm_object=vm_object,
            boot_delay_sec=boot_delay_sec,
        )

        vmware_failover_plan_virtual_machine_model.additional_properties = d
        return vmware_failover_plan_virtual_machine_model

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
