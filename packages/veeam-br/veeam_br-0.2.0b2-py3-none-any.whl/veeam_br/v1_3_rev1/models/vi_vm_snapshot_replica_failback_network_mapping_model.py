from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.inventory_object_model import InventoryObjectModel


T = TypeVar("T", bound="ViVmSnapshotReplicaFailbackNetworkMappingModel")


@_attrs_define
class ViVmSnapshotReplicaFailbackNetworkMappingModel:
    """Network mapping rule.

    Attributes:
        source_network (InventoryObjectModel | Unset): Inventory object properties.
        target_network (InventoryObjectModel | Unset): Inventory object properties.
    """

    source_network: InventoryObjectModel | Unset = UNSET
    target_network: InventoryObjectModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        source_network: dict[str, Any] | Unset = UNSET
        if not isinstance(self.source_network, Unset):
            source_network = self.source_network.to_dict()

        target_network: dict[str, Any] | Unset = UNSET
        if not isinstance(self.target_network, Unset):
            target_network = self.target_network.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if source_network is not UNSET:
            field_dict["sourceNetwork"] = source_network
        if target_network is not UNSET:
            field_dict["targetNetwork"] = target_network

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.inventory_object_model import InventoryObjectModel

        d = dict(src_dict)
        _source_network = d.pop("sourceNetwork", UNSET)
        source_network: InventoryObjectModel | Unset
        if isinstance(_source_network, Unset):
            source_network = UNSET
        else:
            source_network = InventoryObjectModel.from_dict(_source_network)

        _target_network = d.pop("targetNetwork", UNSET)
        target_network: InventoryObjectModel | Unset
        if isinstance(_target_network, Unset):
            target_network = UNSET
        else:
            target_network = InventoryObjectModel.from_dict(_target_network)

        vi_vm_snapshot_replica_failback_network_mapping_model = cls(
            source_network=source_network,
            target_network=target_network,
        )

        vi_vm_snapshot_replica_failback_network_mapping_model.additional_properties = d
        return vi_vm_snapshot_replica_failback_network_mapping_model

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
