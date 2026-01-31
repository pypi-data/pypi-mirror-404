from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="RepositoryShareGatewayImportSpec")


@_attrs_define
class RepositoryShareGatewayImportSpec:
    """Settings for the gateway server.

    Attributes:
        auto_select_enabled (bool | Unset): If `true`, Veeam Backup & Replication automatically selects a gateway
            server.
        gateway_server_name (str | Unset): Name of the gateway server.
    """

    auto_select_enabled: bool | Unset = UNSET
    gateway_server_name: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        auto_select_enabled = self.auto_select_enabled

        gateway_server_name = self.gateway_server_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if auto_select_enabled is not UNSET:
            field_dict["autoSelectEnabled"] = auto_select_enabled
        if gateway_server_name is not UNSET:
            field_dict["gatewayServerName"] = gateway_server_name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        auto_select_enabled = d.pop("autoSelectEnabled", UNSET)

        gateway_server_name = d.pop("gatewayServerName", UNSET)

        repository_share_gateway_import_spec = cls(
            auto_select_enabled=auto_select_enabled,
            gateway_server_name=gateway_server_name,
        )

        repository_share_gateway_import_spec.additional_properties = d
        return repository_share_gateway_import_spec

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
