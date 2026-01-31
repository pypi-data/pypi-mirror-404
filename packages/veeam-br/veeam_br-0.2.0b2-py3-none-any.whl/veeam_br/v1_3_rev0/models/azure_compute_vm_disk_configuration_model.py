from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_azure_compute_vm_disk_type import EAzureComputeVMDiskType
from ..types import UNSET, Unset

T = TypeVar("T", bound="AzureComputeVMDiskConfigurationModel")


@_attrs_define
class AzureComputeVMDiskConfigurationModel:
    """Settings for Microsoft Azure VM disk.

    Attributes:
        disk_uid (str | Unset): Disk UID of the restore point as of which you want to restore your machine. To get the
            UID, run the [Get Restore Point Disks](Restore-Points#operation/GetObjectRestorePointDisks) request.
        disk_type (EAzureComputeVMDiskType | Unset): Disk type of Microsoft Azure VM.
    """

    disk_uid: str | Unset = UNSET
    disk_type: EAzureComputeVMDiskType | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        disk_uid = self.disk_uid

        disk_type: str | Unset = UNSET
        if not isinstance(self.disk_type, Unset):
            disk_type = self.disk_type.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if disk_uid is not UNSET:
            field_dict["diskUid"] = disk_uid
        if disk_type is not UNSET:
            field_dict["diskType"] = disk_type

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        disk_uid = d.pop("diskUid", UNSET)

        _disk_type = d.pop("diskType", UNSET)
        disk_type: EAzureComputeVMDiskType | Unset
        if isinstance(_disk_type, Unset):
            disk_type = UNSET
        else:
            disk_type = EAzureComputeVMDiskType(_disk_type)

        azure_compute_vm_disk_configuration_model = cls(
            disk_uid=disk_uid,
            disk_type=disk_type,
        )

        azure_compute_vm_disk_configuration_model.additional_properties = d
        return azure_compute_vm_disk_configuration_model

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
