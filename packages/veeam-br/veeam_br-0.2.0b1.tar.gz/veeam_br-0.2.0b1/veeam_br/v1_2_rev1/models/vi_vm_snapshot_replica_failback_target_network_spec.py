from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.vi_vm_snapshot_replica_failback_network_mapping_model import (
        ViVmSnapshotReplicaFailbackNetworkMappingModel,
    )


T = TypeVar("T", bound="ViVMSnapshotReplicaFailbackTargetNetworkSpec")


@_attrs_define
class ViVMSnapshotReplicaFailbackTargetNetworkSpec:
    """
    Attributes:
        replica_point_id (UUID | Unset): Restore point ID.
        networks (list[ViVmSnapshotReplicaFailbackNetworkMappingModel] | Unset): Array of network mapping rules. To get
            a network object, use the [Get Inventory Objects](#tag/Inventory-Browser/operation/GetInventoryObjects) request.
    """

    replica_point_id: UUID | Unset = UNSET
    networks: list[ViVmSnapshotReplicaFailbackNetworkMappingModel] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        replica_point_id: str | Unset = UNSET
        if not isinstance(self.replica_point_id, Unset):
            replica_point_id = str(self.replica_point_id)

        networks: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.networks, Unset):
            networks = []
            for networks_item_data in self.networks:
                networks_item = networks_item_data.to_dict()
                networks.append(networks_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if replica_point_id is not UNSET:
            field_dict["replicaPointId"] = replica_point_id
        if networks is not UNSET:
            field_dict["networks"] = networks

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.vi_vm_snapshot_replica_failback_network_mapping_model import (
            ViVmSnapshotReplicaFailbackNetworkMappingModel,
        )

        d = dict(src_dict)
        _replica_point_id = d.pop("replicaPointId", UNSET)
        replica_point_id: UUID | Unset
        if isinstance(_replica_point_id, Unset):
            replica_point_id = UNSET
        else:
            replica_point_id = UUID(_replica_point_id)

        _networks = d.pop("networks", UNSET)
        networks: list[ViVmSnapshotReplicaFailbackNetworkMappingModel] | Unset = UNSET
        if _networks is not UNSET:
            networks = []
            for networks_item_data in _networks:
                networks_item = ViVmSnapshotReplicaFailbackNetworkMappingModel.from_dict(networks_item_data)

                networks.append(networks_item)

        vi_vm_snapshot_replica_failback_target_network_spec = cls(
            replica_point_id=replica_point_id,
            networks=networks,
        )

        vi_vm_snapshot_replica_failback_target_network_spec.additional_properties = d
        return vi_vm_snapshot_replica_failback_target_network_spec

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
