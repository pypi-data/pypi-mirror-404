from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="RepositoryShareGatewayModel")


@_attrs_define
class RepositoryShareGatewayModel:
    """Settings for the gateway server.

    Attributes:
        auto_select_enabled (bool): If `true`, Veeam Backup & Replication automatically selects a gateway server.
        gateway_server_ids (list[UUID] | Unset): Array of gateway server IDs.
    """

    auto_select_enabled: bool
    gateway_server_ids: list[UUID] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        auto_select_enabled = self.auto_select_enabled

        gateway_server_ids: list[str] | Unset = UNSET
        if not isinstance(self.gateway_server_ids, Unset):
            gateway_server_ids = []
            for gateway_server_ids_item_data in self.gateway_server_ids:
                gateway_server_ids_item = str(gateway_server_ids_item_data)
                gateway_server_ids.append(gateway_server_ids_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "autoSelectEnabled": auto_select_enabled,
            }
        )
        if gateway_server_ids is not UNSET:
            field_dict["gatewayServerIds"] = gateway_server_ids

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        auto_select_enabled = d.pop("autoSelectEnabled")

        _gateway_server_ids = d.pop("gatewayServerIds", UNSET)
        gateway_server_ids: list[UUID] | Unset = UNSET
        if _gateway_server_ids is not UNSET:
            gateway_server_ids = []
            for gateway_server_ids_item_data in _gateway_server_ids:
                gateway_server_ids_item = UUID(gateway_server_ids_item_data)

                gateway_server_ids.append(gateway_server_ids_item)

        repository_share_gateway_model = cls(
            auto_select_enabled=auto_select_enabled,
            gateway_server_ids=gateway_server_ids,
        )

        repository_share_gateway_model.additional_properties = d
        return repository_share_gateway_model

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
