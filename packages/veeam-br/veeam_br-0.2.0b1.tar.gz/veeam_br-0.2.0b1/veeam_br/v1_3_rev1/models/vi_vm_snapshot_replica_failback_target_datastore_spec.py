from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.inventory_object_model import InventoryObjectModel
    from ..models.vi_vm_snapshot_replica_failback_target_disk_spec import ViVmSnapshotReplicaFailbackTargetDiskSpec


T = TypeVar("T", bound="ViVMSnapshotReplicaFailbackTargetDatastoreSpec")


@_attrs_define
class ViVMSnapshotReplicaFailbackTargetDatastoreSpec:
    """Target datastore settings.

    Attributes:
        vm_object (InventoryObjectModel | Unset): Inventory object properties.
        disks (list[ViVmSnapshotReplicaFailbackTargetDiskSpec] | Unset): Array of disks that you want to store on the
            specified datastore.
    """

    vm_object: InventoryObjectModel | Unset = UNSET
    disks: list[ViVmSnapshotReplicaFailbackTargetDiskSpec] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        vm_object: dict[str, Any] | Unset = UNSET
        if not isinstance(self.vm_object, Unset):
            vm_object = self.vm_object.to_dict()

        disks: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.disks, Unset):
            disks = []
            for disks_item_data in self.disks:
                disks_item = disks_item_data.to_dict()
                disks.append(disks_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if vm_object is not UNSET:
            field_dict["vmObject"] = vm_object
        if disks is not UNSET:
            field_dict["disks"] = disks

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.inventory_object_model import InventoryObjectModel
        from ..models.vi_vm_snapshot_replica_failback_target_disk_spec import ViVmSnapshotReplicaFailbackTargetDiskSpec

        d = dict(src_dict)
        _vm_object = d.pop("vmObject", UNSET)
        vm_object: InventoryObjectModel | Unset
        if isinstance(_vm_object, Unset):
            vm_object = UNSET
        else:
            vm_object = InventoryObjectModel.from_dict(_vm_object)

        _disks = d.pop("disks", UNSET)
        disks: list[ViVmSnapshotReplicaFailbackTargetDiskSpec] | Unset = UNSET
        if _disks is not UNSET:
            disks = []
            for disks_item_data in _disks:
                disks_item = ViVmSnapshotReplicaFailbackTargetDiskSpec.from_dict(disks_item_data)

                disks.append(disks_item)

        vi_vm_snapshot_replica_failback_target_datastore_spec = cls(
            vm_object=vm_object,
            disks=disks,
        )

        vi_vm_snapshot_replica_failback_target_datastore_spec.additional_properties = d
        return vi_vm_snapshot_replica_failback_target_datastore_spec

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
