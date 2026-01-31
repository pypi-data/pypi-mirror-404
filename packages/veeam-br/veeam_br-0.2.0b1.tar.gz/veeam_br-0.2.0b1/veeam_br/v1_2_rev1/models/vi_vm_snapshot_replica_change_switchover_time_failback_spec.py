from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.replica_failback_mode_spec import ReplicaFailbackModeSpec


T = TypeVar("T", bound="ViVMSnapshotReplicaChangeSwitchoverTimeFailbackSpec")


@_attrs_define
class ViVMSnapshotReplicaChangeSwitchoverTimeFailbackSpec:
    """
    Attributes:
        replica_point_ids (list[UUID] | Unset): Array of replica restore points that you want to change switchover time
            for.
        failback_mode (ReplicaFailbackModeSpec | Unset): Failback mode.
    """

    replica_point_ids: list[UUID] | Unset = UNSET
    failback_mode: ReplicaFailbackModeSpec | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        replica_point_ids: list[str] | Unset = UNSET
        if not isinstance(self.replica_point_ids, Unset):
            replica_point_ids = []
            for replica_point_ids_item_data in self.replica_point_ids:
                replica_point_ids_item = str(replica_point_ids_item_data)
                replica_point_ids.append(replica_point_ids_item)

        failback_mode: dict[str, Any] | Unset = UNSET
        if not isinstance(self.failback_mode, Unset):
            failback_mode = self.failback_mode.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if replica_point_ids is not UNSET:
            field_dict["replicaPointIds"] = replica_point_ids
        if failback_mode is not UNSET:
            field_dict["failbackMode"] = failback_mode

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.replica_failback_mode_spec import ReplicaFailbackModeSpec

        d = dict(src_dict)
        _replica_point_ids = d.pop("replicaPointIds", UNSET)
        replica_point_ids: list[UUID] | Unset = UNSET
        if _replica_point_ids is not UNSET:
            replica_point_ids = []
            for replica_point_ids_item_data in _replica_point_ids:
                replica_point_ids_item = UUID(replica_point_ids_item_data)

                replica_point_ids.append(replica_point_ids_item)

        _failback_mode = d.pop("failbackMode", UNSET)
        failback_mode: ReplicaFailbackModeSpec | Unset
        if isinstance(_failback_mode, Unset):
            failback_mode = UNSET
        else:
            failback_mode = ReplicaFailbackModeSpec.from_dict(_failback_mode)

        vi_vm_snapshot_replica_change_switchover_time_failback_spec = cls(
            replica_point_ids=replica_point_ids,
            failback_mode=failback_mode,
        )

        vi_vm_snapshot_replica_change_switchover_time_failback_spec.additional_properties = d
        return vi_vm_snapshot_replica_change_switchover_time_failback_spec

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
