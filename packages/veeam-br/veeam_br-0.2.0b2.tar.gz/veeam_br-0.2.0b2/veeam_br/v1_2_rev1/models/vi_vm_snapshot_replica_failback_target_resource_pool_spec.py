from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.inventory_object_model import InventoryObjectModel


T = TypeVar("T", bound="ViVMSnapshotReplicaFailbackTargetResourcePoolSpec")


@_attrs_define
class ViVMSnapshotReplicaFailbackTargetResourcePoolSpec:
    """
    Attributes:
        replica_point_id (UUID | Unset): Restore point ID.
        resource_pool (InventoryObjectModel | Unset): Inventory object properties.
    """

    replica_point_id: UUID | Unset = UNSET
    resource_pool: InventoryObjectModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        replica_point_id: str | Unset = UNSET
        if not isinstance(self.replica_point_id, Unset):
            replica_point_id = str(self.replica_point_id)

        resource_pool: dict[str, Any] | Unset = UNSET
        if not isinstance(self.resource_pool, Unset):
            resource_pool = self.resource_pool.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if replica_point_id is not UNSET:
            field_dict["replicaPointId"] = replica_point_id
        if resource_pool is not UNSET:
            field_dict["resourcePool"] = resource_pool

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

        _resource_pool = d.pop("resourcePool", UNSET)
        resource_pool: InventoryObjectModel | Unset
        if isinstance(_resource_pool, Unset):
            resource_pool = UNSET
        else:
            resource_pool = InventoryObjectModel.from_dict(_resource_pool)

        vi_vm_snapshot_replica_failback_target_resource_pool_spec = cls(
            replica_point_id=replica_point_id,
            resource_pool=resource_pool,
        )

        vi_vm_snapshot_replica_failback_target_resource_pool_spec.additional_properties = d
        return vi_vm_snapshot_replica_failback_target_resource_pool_spec

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
