from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="BackupLogShippingServersImportModel")


@_attrs_define
class BackupLogShippingServersImportModel:
    """Log shipping server used to transport logs.

    Attributes:
        auto_select_enabled (bool): If `true`, Veeam Backup & Replication chooses an optimal log shipping server
            automatically.
        shipping_server_names (list[str] | Unset): Array of servers that are explicitly selected for log shipping.
    """

    auto_select_enabled: bool
    shipping_server_names: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        auto_select_enabled = self.auto_select_enabled

        shipping_server_names: list[str] | Unset = UNSET
        if not isinstance(self.shipping_server_names, Unset):
            shipping_server_names = self.shipping_server_names

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "autoSelectEnabled": auto_select_enabled,
            }
        )
        if shipping_server_names is not UNSET:
            field_dict["shippingServerNames"] = shipping_server_names

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        auto_select_enabled = d.pop("autoSelectEnabled")

        shipping_server_names = cast(list[str], d.pop("shippingServerNames", UNSET))

        backup_log_shipping_servers_import_model = cls(
            auto_select_enabled=auto_select_enabled,
            shipping_server_names=shipping_server_names,
        )

        backup_log_shipping_servers_import_model.additional_properties = d
        return backup_log_shipping_servers_import_model

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
