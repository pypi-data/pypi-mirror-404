from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_instant_vi_vm_recovery_bios_uuid_policy_type import EInstantViVmRecoveryBiosUuidPolicyType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.inventory_object_model import InventoryObjectModel


T = TypeVar("T", bound="InstantViVMCustomizedRecoveryDestinationSpec")


@_attrs_define
class InstantViVMCustomizedRecoveryDestinationSpec:
    """Destination where the recovered VM resides. To get objects of the destination host, folder and resource pool, run
    the [Get Inventory Objects](Inventory-Browser#operation/GetInventoryObjects) request.

        Attributes:
            restored_vm_name (str | Unset): Restored VM name.
            destination_host (InventoryObjectModel | Unset): Inventory object properties.
            folder (InventoryObjectModel | Unset): Inventory object properties.
            resource_pool (InventoryObjectModel | Unset): Inventory object properties.
            bios_uuid_policy (EInstantViVmRecoveryBiosUuidPolicyType | Unset): BIOS UUID policy for the restored VM.
    """

    restored_vm_name: str | Unset = UNSET
    destination_host: InventoryObjectModel | Unset = UNSET
    folder: InventoryObjectModel | Unset = UNSET
    resource_pool: InventoryObjectModel | Unset = UNSET
    bios_uuid_policy: EInstantViVmRecoveryBiosUuidPolicyType | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        restored_vm_name = self.restored_vm_name

        destination_host: dict[str, Any] | Unset = UNSET
        if not isinstance(self.destination_host, Unset):
            destination_host = self.destination_host.to_dict()

        folder: dict[str, Any] | Unset = UNSET
        if not isinstance(self.folder, Unset):
            folder = self.folder.to_dict()

        resource_pool: dict[str, Any] | Unset = UNSET
        if not isinstance(self.resource_pool, Unset):
            resource_pool = self.resource_pool.to_dict()

        bios_uuid_policy: str | Unset = UNSET
        if not isinstance(self.bios_uuid_policy, Unset):
            bios_uuid_policy = self.bios_uuid_policy.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if restored_vm_name is not UNSET:
            field_dict["restoredVmName"] = restored_vm_name
        if destination_host is not UNSET:
            field_dict["destinationHost"] = destination_host
        if folder is not UNSET:
            field_dict["folder"] = folder
        if resource_pool is not UNSET:
            field_dict["resourcePool"] = resource_pool
        if bios_uuid_policy is not UNSET:
            field_dict["biosUuidPolicy"] = bios_uuid_policy

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.inventory_object_model import InventoryObjectModel

        d = dict(src_dict)
        restored_vm_name = d.pop("restoredVmName", UNSET)

        _destination_host = d.pop("destinationHost", UNSET)
        destination_host: InventoryObjectModel | Unset
        if isinstance(_destination_host, Unset):
            destination_host = UNSET
        else:
            destination_host = InventoryObjectModel.from_dict(_destination_host)

        _folder = d.pop("folder", UNSET)
        folder: InventoryObjectModel | Unset
        if isinstance(_folder, Unset):
            folder = UNSET
        else:
            folder = InventoryObjectModel.from_dict(_folder)

        _resource_pool = d.pop("resourcePool", UNSET)
        resource_pool: InventoryObjectModel | Unset
        if isinstance(_resource_pool, Unset):
            resource_pool = UNSET
        else:
            resource_pool = InventoryObjectModel.from_dict(_resource_pool)

        _bios_uuid_policy = d.pop("biosUuidPolicy", UNSET)
        bios_uuid_policy: EInstantViVmRecoveryBiosUuidPolicyType | Unset
        if isinstance(_bios_uuid_policy, Unset):
            bios_uuid_policy = UNSET
        else:
            bios_uuid_policy = EInstantViVmRecoveryBiosUuidPolicyType(_bios_uuid_policy)

        instant_vi_vm_customized_recovery_destination_spec = cls(
            restored_vm_name=restored_vm_name,
            destination_host=destination_host,
            folder=folder,
            resource_pool=resource_pool,
            bios_uuid_policy=bios_uuid_policy,
        )

        instant_vi_vm_customized_recovery_destination_spec.additional_properties = d
        return instant_vi_vm_customized_recovery_destination_spec

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
