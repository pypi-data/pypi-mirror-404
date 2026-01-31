from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.azure_compute_vm_disk_configuration_model import AzureComputeVMDiskConfigurationModel


T = TypeVar("T", bound="AzureComputeVMSizeModel")


@_attrs_define
class AzureComputeVMSizeModel:
    """Size settings for Microsoft Azure VM.

    Attributes:
        instance_size (str): Microsoft Azure VM size identifier, indicating the VM CPU, memory, and storage
            capabilities. For example, `Standard_F4s_v2` provides 4 CPU cores, 8 GB RAM, and premium SSD support.
        disks (list[AzureComputeVMDiskConfigurationModel] | Unset): Array of objects containing settings for Microsoft
            Azure VM disks.
    """

    instance_size: str
    disks: list[AzureComputeVMDiskConfigurationModel] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        instance_size = self.instance_size

        disks: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.disks, Unset):
            disks = []
            for disks_item_data in self.disks:
                disks_item = disks_item_data.to_dict()
                disks.append(disks_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "instanceSize": instance_size,
            }
        )
        if disks is not UNSET:
            field_dict["disks"] = disks

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.azure_compute_vm_disk_configuration_model import AzureComputeVMDiskConfigurationModel

        d = dict(src_dict)
        instance_size = d.pop("instanceSize")

        _disks = d.pop("disks", UNSET)
        disks: list[AzureComputeVMDiskConfigurationModel] | Unset = UNSET
        if _disks is not UNSET:
            disks = []
            for disks_item_data in _disks:
                disks_item = AzureComputeVMDiskConfigurationModel.from_dict(disks_item_data)

                disks.append(disks_item)

        azure_compute_vm_size_model = cls(
            instance_size=instance_size,
            disks=disks,
        )

        azure_compute_vm_size_model.additional_properties = d
        return azure_compute_vm_size_model

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
