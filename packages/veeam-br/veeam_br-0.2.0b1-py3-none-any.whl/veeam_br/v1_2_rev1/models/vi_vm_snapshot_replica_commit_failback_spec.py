from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ViVMSnapshotReplicaCommitFailbackSpec")


@_attrs_define
class ViVMSnapshotReplicaCommitFailbackSpec:
    """
    Attributes:
        replica_point_ids (list[UUID] | Unset): Array of replica restore points that you want to commit failback for.
    """

    replica_point_ids: list[UUID] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        replica_point_ids: list[str] | Unset = UNSET
        if not isinstance(self.replica_point_ids, Unset):
            replica_point_ids = []
            for replica_point_ids_item_data in self.replica_point_ids:
                replica_point_ids_item = str(replica_point_ids_item_data)
                replica_point_ids.append(replica_point_ids_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if replica_point_ids is not UNSET:
            field_dict["replicaPointIds"] = replica_point_ids

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _replica_point_ids = d.pop("replicaPointIds", UNSET)
        replica_point_ids: list[UUID] | Unset = UNSET
        if _replica_point_ids is not UNSET:
            replica_point_ids = []
            for replica_point_ids_item_data in _replica_point_ids:
                replica_point_ids_item = UUID(replica_point_ids_item_data)

                replica_point_ids.append(replica_point_ids_item)

        vi_vm_snapshot_replica_commit_failback_spec = cls(
            replica_point_ids=replica_point_ids,
        )

        vi_vm_snapshot_replica_commit_failback_spec.additional_properties = d
        return vi_vm_snapshot_replica_commit_failback_spec

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
