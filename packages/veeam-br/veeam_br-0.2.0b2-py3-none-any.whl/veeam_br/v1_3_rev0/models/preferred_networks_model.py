from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.preferred_network_model import PreferredNetworkModel


T = TypeVar("T", bound="PreferredNetworksModel")


@_attrs_define
class PreferredNetworksModel:
    """Preferred networks used for backup and replication traffic.

    Attributes:
        is_enabled (bool): If `true`, preferred networks are enabled.
        networks (list[PreferredNetworkModel] | Unset): Array of networks.
    """

    is_enabled: bool
    networks: list[PreferredNetworkModel] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        is_enabled = self.is_enabled

        networks: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.networks, Unset):
            networks = []
            for networks_item_data in self.networks:
                networks_item = networks_item_data.to_dict()
                networks.append(networks_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "isEnabled": is_enabled,
            }
        )
        if networks is not UNSET:
            field_dict["networks"] = networks

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.preferred_network_model import PreferredNetworkModel

        d = dict(src_dict)
        is_enabled = d.pop("isEnabled")

        _networks = d.pop("networks", UNSET)
        networks: list[PreferredNetworkModel] | Unset = UNSET
        if _networks is not UNSET:
            networks = []
            for networks_item_data in _networks:
                networks_item = PreferredNetworkModel.from_dict(networks_item_data)

                networks.append(networks_item)

        preferred_networks_model = cls(
            is_enabled=is_enabled,
            networks=networks,
        )

        preferred_networks_model.additional_properties = d
        return preferred_networks_model

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
