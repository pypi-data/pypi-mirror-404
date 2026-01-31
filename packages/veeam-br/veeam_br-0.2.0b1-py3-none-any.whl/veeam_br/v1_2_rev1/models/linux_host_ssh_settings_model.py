from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="LinuxHostSSHSettingsModel")


@_attrs_define
class LinuxHostSSHSettingsModel:
    """SSH settings.

    Attributes:
        ssh_time_out_ms (int | Unset): SSH timeout, in ms. If a task targeted at the server is inactive after the
            timeout, the task is terminated.
        port_range_start (int | Unset): Start port used for data transfer.
        port_range_end (int | Unset): End port used for data transfer.
        server_side (bool | Unset): If `true`, the server is run on this side.
        management_port (int | Unset): Port used as a control channel from the Veeam Backup & Replication console to the
            Linux server.
    """

    ssh_time_out_ms: int | Unset = UNSET
    port_range_start: int | Unset = UNSET
    port_range_end: int | Unset = UNSET
    server_side: bool | Unset = UNSET
    management_port: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        ssh_time_out_ms = self.ssh_time_out_ms

        port_range_start = self.port_range_start

        port_range_end = self.port_range_end

        server_side = self.server_side

        management_port = self.management_port

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if ssh_time_out_ms is not UNSET:
            field_dict["sshTimeOutMs"] = ssh_time_out_ms
        if port_range_start is not UNSET:
            field_dict["portRangeStart"] = port_range_start
        if port_range_end is not UNSET:
            field_dict["portRangeEnd"] = port_range_end
        if server_side is not UNSET:
            field_dict["serverSide"] = server_side
        if management_port is not UNSET:
            field_dict["managementPort"] = management_port

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        ssh_time_out_ms = d.pop("sshTimeOutMs", UNSET)

        port_range_start = d.pop("portRangeStart", UNSET)

        port_range_end = d.pop("portRangeEnd", UNSET)

        server_side = d.pop("serverSide", UNSET)

        management_port = d.pop("managementPort", UNSET)

        linux_host_ssh_settings_model = cls(
            ssh_time_out_ms=ssh_time_out_ms,
            port_range_start=port_range_start,
            port_range_end=port_range_end,
            server_side=server_side,
            management_port=management_port,
        )

        linux_host_ssh_settings_model.additional_properties = d
        return linux_host_ssh_settings_model

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
