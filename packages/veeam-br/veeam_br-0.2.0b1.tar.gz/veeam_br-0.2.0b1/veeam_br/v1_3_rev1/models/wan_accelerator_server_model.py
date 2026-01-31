from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="WANAcceleratorServerModel")


@_attrs_define
class WANAcceleratorServerModel:
    """Microsoft Windows server used as a WAN accelerator.

    Attributes:
        host_id (UUID | Unset): Server ID.
        description (str | Unset): WAN accelerator description.
        traffic_port (int | Unset): Number of the port used for communication with other WAN accelerators.
        streams_count (int | Unset): Number of connections that are used to transmit data between WAN accelerators. This
            setting applies only to the source WAN accelerator.
        high_bandwidth_mode_enabled (bool | Unset): If `true`, the high bandwidth mode is enabled.
    """

    host_id: UUID | Unset = UNSET
    description: str | Unset = UNSET
    traffic_port: int | Unset = UNSET
    streams_count: int | Unset = UNSET
    high_bandwidth_mode_enabled: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        host_id: str | Unset = UNSET
        if not isinstance(self.host_id, Unset):
            host_id = str(self.host_id)

        description = self.description

        traffic_port = self.traffic_port

        streams_count = self.streams_count

        high_bandwidth_mode_enabled = self.high_bandwidth_mode_enabled

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if host_id is not UNSET:
            field_dict["hostId"] = host_id
        if description is not UNSET:
            field_dict["description"] = description
        if traffic_port is not UNSET:
            field_dict["trafficPort"] = traffic_port
        if streams_count is not UNSET:
            field_dict["streamsCount"] = streams_count
        if high_bandwidth_mode_enabled is not UNSET:
            field_dict["highBandwidthModeEnabled"] = high_bandwidth_mode_enabled

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _host_id = d.pop("hostId", UNSET)
        host_id: UUID | Unset
        if isinstance(_host_id, Unset):
            host_id = UNSET
        else:
            host_id = UUID(_host_id)

        description = d.pop("description", UNSET)

        traffic_port = d.pop("trafficPort", UNSET)

        streams_count = d.pop("streamsCount", UNSET)

        high_bandwidth_mode_enabled = d.pop("highBandwidthModeEnabled", UNSET)

        wan_accelerator_server_model = cls(
            host_id=host_id,
            description=description,
            traffic_port=traffic_port,
            streams_count=streams_count,
            high_bandwidth_mode_enabled=high_bandwidth_mode_enabled,
        )

        wan_accelerator_server_model.additional_properties = d
        return wan_accelerator_server_model

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
