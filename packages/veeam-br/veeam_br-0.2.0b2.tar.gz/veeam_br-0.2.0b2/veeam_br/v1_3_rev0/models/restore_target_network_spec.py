from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.restore_target_network_mapping_model import RestoreTargetNetworkMappingModel


T = TypeVar("T", bound="RestoreTargetNetworkSpec")


@_attrs_define
class RestoreTargetNetworkSpec:
    """Network to which the restored VM will be connected. To get a network object, use the [Get Inventory
    Objects](Inventory-Browser#operation/GetInventoryObjects) request.

        Attributes:
            networks (list[RestoreTargetNetworkMappingModel]): Array of network mapping rules. To get a network object, use
                the [Get Inventory Objects](Inventory-Browser#operation/GetInventoryObjects) request.
            disconnected (bool | Unset): If `true`, the restored VMs is not connected to any virtual network.
    """

    networks: list[RestoreTargetNetworkMappingModel]
    disconnected: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        networks = []
        for networks_item_data in self.networks:
            networks_item = networks_item_data.to_dict()
            networks.append(networks_item)

        disconnected = self.disconnected

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "networks": networks,
            }
        )
        if disconnected is not UNSET:
            field_dict["disconnected"] = disconnected

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.restore_target_network_mapping_model import RestoreTargetNetworkMappingModel

        d = dict(src_dict)
        networks = []
        _networks = d.pop("networks")
        for networks_item_data in _networks:
            networks_item = RestoreTargetNetworkMappingModel.from_dict(networks_item_data)

            networks.append(networks_item)

        disconnected = d.pop("disconnected", UNSET)

        restore_target_network_spec = cls(
            networks=networks,
            disconnected=disconnected,
        )

        restore_target_network_spec.additional_properties = d
        return restore_target_network_spec

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
