from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="HvHostDiscoverySpec")


@_attrs_define
class HvHostDiscoverySpec:
    """Settings for Microsoft Hyper-V hosts discovery.

    Attributes:
        credentials_id (UUID | Unset): Credentials ID used to connect to the Microsoft Hyper-V cluster or SCVMM Server.
        scvmm_host_id (UUID | Unset): ID of the SCVMM server.
        hv_cluster_name (str | Unset): Name of the Microsoft Hyper-V cluster.
    """

    credentials_id: UUID | Unset = UNSET
    scvmm_host_id: UUID | Unset = UNSET
    hv_cluster_name: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        credentials_id: str | Unset = UNSET
        if not isinstance(self.credentials_id, Unset):
            credentials_id = str(self.credentials_id)

        scvmm_host_id: str | Unset = UNSET
        if not isinstance(self.scvmm_host_id, Unset):
            scvmm_host_id = str(self.scvmm_host_id)

        hv_cluster_name = self.hv_cluster_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if credentials_id is not UNSET:
            field_dict["credentialsId"] = credentials_id
        if scvmm_host_id is not UNSET:
            field_dict["scvmmHostId"] = scvmm_host_id
        if hv_cluster_name is not UNSET:
            field_dict["hvClusterName"] = hv_cluster_name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _credentials_id = d.pop("credentialsId", UNSET)
        credentials_id: UUID | Unset
        if isinstance(_credentials_id, Unset):
            credentials_id = UNSET
        else:
            credentials_id = UUID(_credentials_id)

        _scvmm_host_id = d.pop("scvmmHostId", UNSET)
        scvmm_host_id: UUID | Unset
        if isinstance(_scvmm_host_id, Unset):
            scvmm_host_id = UNSET
        else:
            scvmm_host_id = UUID(_scvmm_host_id)

        hv_cluster_name = d.pop("hvClusterName", UNSET)

        hv_host_discovery_spec = cls(
            credentials_id=credentials_id,
            scvmm_host_id=scvmm_host_id,
            hv_cluster_name=hv_cluster_name,
        )

        hv_host_discovery_spec.additional_properties = d
        return hv_host_discovery_spec

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
