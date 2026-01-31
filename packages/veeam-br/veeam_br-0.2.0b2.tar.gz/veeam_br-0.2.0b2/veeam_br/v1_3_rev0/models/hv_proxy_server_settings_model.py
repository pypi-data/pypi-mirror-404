from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="HvProxyServerSettingsModel")


@_attrs_define
class HvProxyServerSettingsModel:
    """Settings for the Microsoft Hyper-V off-host backup proxy.

    Attributes:
        host_id (UUID): ID of the server.
        host_name (str | Unset): Name of the server.
        max_task_count (int | Unset): Maximum number of concurrent tasks.
    """

    host_id: UUID
    host_name: str | Unset = UNSET
    max_task_count: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        host_id = str(self.host_id)

        host_name = self.host_name

        max_task_count = self.max_task_count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "hostId": host_id,
            }
        )
        if host_name is not UNSET:
            field_dict["hostName"] = host_name
        if max_task_count is not UNSET:
            field_dict["maxTaskCount"] = max_task_count

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        host_id = UUID(d.pop("hostId"))

        host_name = d.pop("hostName", UNSET)

        max_task_count = d.pop("maxTaskCount", UNSET)

        hv_proxy_server_settings_model = cls(
            host_id=host_id,
            host_name=host_name,
            max_task_count=max_task_count,
        )

        hv_proxy_server_settings_model.additional_properties = d
        return hv_proxy_server_settings_model

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
