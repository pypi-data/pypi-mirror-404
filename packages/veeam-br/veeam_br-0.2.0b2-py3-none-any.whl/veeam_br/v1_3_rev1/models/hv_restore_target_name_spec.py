from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="HvRestoreTargetNameSpec")


@_attrs_define
class HvRestoreTargetNameSpec:
    """Destination VM folder.

    Attributes:
        vm_name (str | Unset): Name of the restored VM. Note that if you do not specify a value for this property, Veeam
            Backup & Replication will use the original VM name.
        preserve_uuid (bool | Unset): If `true`, the BIOS UUID of the source VM is used.
        register_as_cluster_resource (bool | Unset): If `true`, the restored VM is configured as a cluster resource. In
            this case, if the target host is offline or fails for any reason, the VM will fail over to another node in the
            cluster.
        overwrite_existing_vm (bool | Unset): If `true`, the existing VM with the same name is overwritten.
        overwrite_existing_disks (bool | Unset): If `true`, the existing VM disks with the same names are overwritten.
    """

    vm_name: str | Unset = UNSET
    preserve_uuid: bool | Unset = UNSET
    register_as_cluster_resource: bool | Unset = UNSET
    overwrite_existing_vm: bool | Unset = UNSET
    overwrite_existing_disks: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        vm_name = self.vm_name

        preserve_uuid = self.preserve_uuid

        register_as_cluster_resource = self.register_as_cluster_resource

        overwrite_existing_vm = self.overwrite_existing_vm

        overwrite_existing_disks = self.overwrite_existing_disks

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if vm_name is not UNSET:
            field_dict["vmName"] = vm_name
        if preserve_uuid is not UNSET:
            field_dict["preserveUUID"] = preserve_uuid
        if register_as_cluster_resource is not UNSET:
            field_dict["registerAsClusterResource"] = register_as_cluster_resource
        if overwrite_existing_vm is not UNSET:
            field_dict["overwriteExistingVm"] = overwrite_existing_vm
        if overwrite_existing_disks is not UNSET:
            field_dict["overwriteExistingDisks"] = overwrite_existing_disks

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        vm_name = d.pop("vmName", UNSET)

        preserve_uuid = d.pop("preserveUUID", UNSET)

        register_as_cluster_resource = d.pop("registerAsClusterResource", UNSET)

        overwrite_existing_vm = d.pop("overwriteExistingVm", UNSET)

        overwrite_existing_disks = d.pop("overwriteExistingDisks", UNSET)

        hv_restore_target_name_spec = cls(
            vm_name=vm_name,
            preserve_uuid=preserve_uuid,
            register_as_cluster_resource=register_as_cluster_resource,
            overwrite_existing_vm=overwrite_existing_vm,
            overwrite_existing_disks=overwrite_existing_disks,
        )

        hv_restore_target_name_spec.additional_properties = d
        return hv_restore_target_name_spec

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
