from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_hyper_v_disks_type_to_process import EHyperVDisksTypeToProcess

if TYPE_CHECKING:
    from ..models.inventory_object_model import InventoryObjectModel


T = TypeVar("T", bound="HyperVObjectDiskModel")


@_attrs_define
class HyperVObjectDiskModel:
    """Disk settings for Microsoft Hyper-V object.

    Attributes:
        vm_object (InventoryObjectModel): Inventory object properties.
        disks_to_process (EHyperVDisksTypeToProcess): Type of disk selection.
        disks (list[str]): Array of disks.
    """

    vm_object: InventoryObjectModel
    disks_to_process: EHyperVDisksTypeToProcess
    disks: list[str]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        vm_object = self.vm_object.to_dict()

        disks_to_process = self.disks_to_process.value

        disks = self.disks

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "vmObject": vm_object,
                "disksToProcess": disks_to_process,
                "disks": disks,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.inventory_object_model import InventoryObjectModel

        d = dict(src_dict)
        vm_object = InventoryObjectModel.from_dict(d.pop("vmObject"))

        disks_to_process = EHyperVDisksTypeToProcess(d.pop("disksToProcess"))

        disks = cast(list[str], d.pop("disks"))

        hyper_v_object_disk_model = cls(
            vm_object=vm_object,
            disks_to_process=disks_to_process,
            disks=disks,
        )

        hyper_v_object_disk_model.additional_properties = d
        return hyper_v_object_disk_model

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
