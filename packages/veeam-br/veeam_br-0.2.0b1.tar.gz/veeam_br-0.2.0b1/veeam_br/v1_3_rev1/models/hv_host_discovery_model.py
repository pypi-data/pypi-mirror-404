from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="HvHostDiscoveryModel")


@_attrs_define
class HvHostDiscoveryModel:
    """Microsoft Hyper-V server.

    Attributes:
        hv_server_name (str): Name of the Microsoft Hyper-V server.
    """

    hv_server_name: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        hv_server_name = self.hv_server_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "hvServerName": hv_server_name,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        hv_server_name = d.pop("hvServerName")

        hv_host_discovery_model = cls(
            hv_server_name=hv_server_name,
        )

        hv_host_discovery_model.additional_properties = d
        return hv_host_discovery_model

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
