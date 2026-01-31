from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ReplicaRescanSpec")


@_attrs_define
class ReplicaRescanSpec:
    """Replica rescan settings.

    Attributes:
        replica_ids (list[UUID] | Unset): Array of replica IDs that you want to rescan. To get the IDs, run the [Get All
            Replicas](Replicas#operation/GetAllReplicas) request.
    """

    replica_ids: list[UUID] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        replica_ids: list[str] | Unset = UNSET
        if not isinstance(self.replica_ids, Unset):
            replica_ids = []
            for replica_ids_item_data in self.replica_ids:
                replica_ids_item = str(replica_ids_item_data)
                replica_ids.append(replica_ids_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if replica_ids is not UNSET:
            field_dict["replicaIds"] = replica_ids

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _replica_ids = d.pop("replicaIds", UNSET)
        replica_ids: list[UUID] | Unset = UNSET
        if _replica_ids is not UNSET:
            replica_ids = []
            for replica_ids_item_data in _replica_ids:
                replica_ids_item = UUID(replica_ids_item_data)

                replica_ids.append(replica_ids_item)

        replica_rescan_spec = cls(
            replica_ids=replica_ids,
        )

        replica_rescan_spec.additional_properties = d
        return replica_rescan_spec

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
