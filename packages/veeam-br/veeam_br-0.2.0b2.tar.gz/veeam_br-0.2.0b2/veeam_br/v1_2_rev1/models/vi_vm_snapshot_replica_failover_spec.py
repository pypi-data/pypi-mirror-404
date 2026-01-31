from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ViVMSnapshotReplicaFailoverSpec")


@_attrs_define
class ViVMSnapshotReplicaFailoverSpec:
    """
    Attributes:
        replica_point_ids (list[UUID]): Array of replica restore points.
        reason (str | Unset): Operation reason.
    """

    replica_point_ids: list[UUID]
    reason: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        replica_point_ids = []
        for replica_point_ids_item_data in self.replica_point_ids:
            replica_point_ids_item = str(replica_point_ids_item_data)
            replica_point_ids.append(replica_point_ids_item)

        reason = self.reason

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "replicaPointIds": replica_point_ids,
            }
        )
        if reason is not UNSET:
            field_dict["reason"] = reason

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        replica_point_ids = []
        _replica_point_ids = d.pop("replicaPointIds")
        for replica_point_ids_item_data in _replica_point_ids:
            replica_point_ids_item = UUID(replica_point_ids_item_data)

            replica_point_ids.append(replica_point_ids_item)

        reason = d.pop("reason", UNSET)

        vi_vm_snapshot_replica_failover_spec = cls(
            replica_point_ids=replica_point_ids,
            reason=reason,
        )

        vi_vm_snapshot_replica_failover_spec.additional_properties = d
        return vi_vm_snapshot_replica_failover_spec

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
