from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.inventory_object_model import InventoryObjectModel


T = TypeVar("T", bound="RestoreTargetNetworkSpec")


@_attrs_define
class RestoreTargetNetworkSpec:
    """Network that the restored VM will be connected to. To get a network object, use the [Get Inventory
    Objects](#tag/Inventory-Browser/operation/GetInventoryObjects) request.

        Attributes:
            network (InventoryObjectModel): Inventory object properties.
            disconnected (bool | Unset): If `true`, the restored VMs is not connected to any virtual network.
    """

    network: InventoryObjectModel
    disconnected: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        network = self.network.to_dict()

        disconnected = self.disconnected

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "network": network,
            }
        )
        if disconnected is not UNSET:
            field_dict["disconnected"] = disconnected

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.inventory_object_model import InventoryObjectModel

        d = dict(src_dict)
        network = InventoryObjectModel.from_dict(d.pop("network"))

        disconnected = d.pop("disconnected", UNSET)

        restore_target_network_spec = cls(
            network=network,
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
