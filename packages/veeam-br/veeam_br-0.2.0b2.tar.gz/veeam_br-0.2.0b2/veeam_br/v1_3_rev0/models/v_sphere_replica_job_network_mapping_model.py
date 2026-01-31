from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.inventory_object_model import InventoryObjectModel


T = TypeVar("T", bound="VSphereReplicaJobNetworkMappingModel")


@_attrs_define
class VSphereReplicaJobNetworkMappingModel:
    """Network mapping rule.

    Attributes:
        source_network (InventoryObjectModel): Inventory object properties.
        target_network (InventoryObjectModel): Inventory object properties.
    """

    source_network: InventoryObjectModel
    target_network: InventoryObjectModel
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        source_network = self.source_network.to_dict()

        target_network = self.target_network.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "sourceNetwork": source_network,
                "targetNetwork": target_network,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.inventory_object_model import InventoryObjectModel

        d = dict(src_dict)
        source_network = InventoryObjectModel.from_dict(d.pop("sourceNetwork"))

        target_network = InventoryObjectModel.from_dict(d.pop("targetNetwork"))

        v_sphere_replica_job_network_mapping_model = cls(
            source_network=source_network,
            target_network=target_network,
        )

        v_sphere_replica_job_network_mapping_model.additional_properties = d
        return v_sphere_replica_job_network_mapping_model

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
