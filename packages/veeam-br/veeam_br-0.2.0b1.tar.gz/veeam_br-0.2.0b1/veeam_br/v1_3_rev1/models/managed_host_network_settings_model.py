from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ManagedHostNetworkSettingsModel")


@_attrs_define
class ManagedHostNetworkSettingsModel:
    """Veeam Backup & Replication components installed on the server and ports used by the components.

    Attributes:
        port_range_start (int | Unset): Start port used for data transfer.
        port_range_end (int | Unset): End port used for data transfer.
        server_side (bool | Unset): If `true`, the server is run on this side.
    """

    port_range_start: int | Unset = UNSET
    port_range_end: int | Unset = UNSET
    server_side: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        port_range_start = self.port_range_start

        port_range_end = self.port_range_end

        server_side = self.server_side

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if port_range_start is not UNSET:
            field_dict["portRangeStart"] = port_range_start
        if port_range_end is not UNSET:
            field_dict["portRangeEnd"] = port_range_end
        if server_side is not UNSET:
            field_dict["serverSide"] = server_side

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        port_range_start = d.pop("portRangeStart", UNSET)

        port_range_end = d.pop("portRangeEnd", UNSET)

        server_side = d.pop("serverSide", UNSET)

        managed_host_network_settings_model = cls(
            port_range_start=port_range_start,
            port_range_end=port_range_end,
            server_side=server_side,
        )

        managed_host_network_settings_model.additional_properties = d
        return managed_host_network_settings_model

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
