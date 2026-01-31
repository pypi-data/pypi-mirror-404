from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.inventory_object_model import InventoryObjectModel


T = TypeVar("T", bound="ViVMSnapshotReplicaFailbackTargetVMSpec")


@_attrs_define
class ViVMSnapshotReplicaFailbackTargetVMSpec:
    """Target VM settings.

    Attributes:
        replica_point_id (UUID | Unset): Restore point ID.
        destination_vm (InventoryObjectModel | Unset): Inventory object properties.
    """

    replica_point_id: UUID | Unset = UNSET
    destination_vm: InventoryObjectModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        replica_point_id: str | Unset = UNSET
        if not isinstance(self.replica_point_id, Unset):
            replica_point_id = str(self.replica_point_id)

        destination_vm: dict[str, Any] | Unset = UNSET
        if not isinstance(self.destination_vm, Unset):
            destination_vm = self.destination_vm.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if replica_point_id is not UNSET:
            field_dict["replicaPointId"] = replica_point_id
        if destination_vm is not UNSET:
            field_dict["destinationVM"] = destination_vm

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.inventory_object_model import InventoryObjectModel

        d = dict(src_dict)
        _replica_point_id = d.pop("replicaPointId", UNSET)
        replica_point_id: UUID | Unset
        if isinstance(_replica_point_id, Unset):
            replica_point_id = UNSET
        else:
            replica_point_id = UUID(_replica_point_id)

        _destination_vm = d.pop("destinationVM", UNSET)
        destination_vm: InventoryObjectModel | Unset
        if isinstance(_destination_vm, Unset):
            destination_vm = UNSET
        else:
            destination_vm = InventoryObjectModel.from_dict(_destination_vm)

        vi_vm_snapshot_replica_failback_target_vm_spec = cls(
            replica_point_id=replica_point_id,
            destination_vm=destination_vm,
        )

        vi_vm_snapshot_replica_failback_target_vm_spec.additional_properties = d
        return vi_vm_snapshot_replica_failback_target_vm_spec

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
