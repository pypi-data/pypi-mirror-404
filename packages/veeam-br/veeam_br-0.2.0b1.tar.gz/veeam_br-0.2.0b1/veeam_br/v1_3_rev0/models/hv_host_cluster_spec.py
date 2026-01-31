from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_managed_server_type import EManagedServerType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.hv_host_discovery_model import HvHostDiscoveryModel
    from ..models.managed_host_network_settings_model import ManagedHostNetworkSettingsModel


T = TypeVar("T", bound="HvHostClusterSpec")


@_attrs_define
class HvHostClusterSpec:
    """Microsoft Hyper-V cluster settings.

    Attributes:
        name (str): Full DNS name or IP address of the server.
        description (str): Description of the server.
        type_ (EManagedServerType): Type of the server.
        credentials_id (UUID): ID of the credentials used to connect to the cluster.
        network_settings (ManagedHostNetworkSettingsModel | Unset): Veeam Backup & Replication components installed on
            the server and ports used by the components.
        hv_servers (list[HvHostDiscoveryModel] | Unset): Array of Microsoft Hyper-V servers belonged to the cluster that
            you want to add to Veeam Backup & Replication. If you skip this property, all cluster hosts will be added.
    """

    name: str
    description: str
    type_: EManagedServerType
    credentials_id: UUID
    network_settings: ManagedHostNetworkSettingsModel | Unset = UNSET
    hv_servers: list[HvHostDiscoveryModel] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        description = self.description

        type_ = self.type_.value

        credentials_id = str(self.credentials_id)

        network_settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.network_settings, Unset):
            network_settings = self.network_settings.to_dict()

        hv_servers: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.hv_servers, Unset):
            hv_servers = []
            for hv_servers_item_data in self.hv_servers:
                hv_servers_item = hv_servers_item_data.to_dict()
                hv_servers.append(hv_servers_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "description": description,
                "type": type_,
                "credentialsId": credentials_id,
            }
        )
        if network_settings is not UNSET:
            field_dict["networkSettings"] = network_settings
        if hv_servers is not UNSET:
            field_dict["hvServers"] = hv_servers

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.hv_host_discovery_model import HvHostDiscoveryModel
        from ..models.managed_host_network_settings_model import ManagedHostNetworkSettingsModel

        d = dict(src_dict)
        name = d.pop("name")

        description = d.pop("description")

        type_ = EManagedServerType(d.pop("type"))

        credentials_id = UUID(d.pop("credentialsId"))

        _network_settings = d.pop("networkSettings", UNSET)
        network_settings: ManagedHostNetworkSettingsModel | Unset
        if isinstance(_network_settings, Unset):
            network_settings = UNSET
        else:
            network_settings = ManagedHostNetworkSettingsModel.from_dict(_network_settings)

        _hv_servers = d.pop("hvServers", UNSET)
        hv_servers: list[HvHostDiscoveryModel] | Unset = UNSET
        if _hv_servers is not UNSET:
            hv_servers = []
            for hv_servers_item_data in _hv_servers:
                hv_servers_item = HvHostDiscoveryModel.from_dict(hv_servers_item_data)

                hv_servers.append(hv_servers_item)

        hv_host_cluster_spec = cls(
            name=name,
            description=description,
            type_=type_,
            credentials_id=credentials_id,
            network_settings=network_settings,
            hv_servers=hv_servers,
        )

        hv_host_cluster_spec.additional_properties = d
        return hv_host_cluster_spec

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
