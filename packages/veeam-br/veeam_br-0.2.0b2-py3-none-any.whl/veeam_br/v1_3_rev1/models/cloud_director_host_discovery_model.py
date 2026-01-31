from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CloudDirectorHostDiscoveryModel")


@_attrs_define
class CloudDirectorHostDiscoveryModel:
    """Overview of VMware Cloud Director server.

    Attributes:
        vi_server_name (str): Name of VMware vCenter Server.
        certificate_thumbprint (str | Unset): Certificate thumbprint used to verify the server identity.
    """

    vi_server_name: str
    certificate_thumbprint: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        vi_server_name = self.vi_server_name

        certificate_thumbprint = self.certificate_thumbprint

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "viServerName": vi_server_name,
            }
        )
        if certificate_thumbprint is not UNSET:
            field_dict["certificateThumbprint"] = certificate_thumbprint

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        vi_server_name = d.pop("viServerName")

        certificate_thumbprint = d.pop("certificateThumbprint", UNSET)

        cloud_director_host_discovery_model = cls(
            vi_server_name=vi_server_name,
            certificate_thumbprint=certificate_thumbprint,
        )

        cloud_director_host_discovery_model.additional_properties = d
        return cloud_director_host_discovery_model

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
