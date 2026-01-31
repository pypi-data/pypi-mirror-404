from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_managed_server_type import EManagedServerType
from ..models.e_managed_servers_status import EManagedServersStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.hv_host_discovery_model import HvHostDiscoveryModel
    from ..models.managed_host_network_settings_model import ManagedHostNetworkSettingsModel


T = TypeVar("T", bound="HvHostClusterModel")


@_attrs_define
class HvHostClusterModel:
    """Microsoft Hyper-V cluster.

    Attributes:
        id (UUID): ID of the server.
        name (str): Full DNS name or IP address of the server.
        description (str): Description of the server.
        type_ (EManagedServerType): Type of the server.
        status (EManagedServersStatus): Availability status.
        credentials_id (UUID): ID of the credentials used to connect to the cluster.
        network_settings (ManagedHostNetworkSettingsModel | Unset): Veeam Backup & Replication components installed on
            the server and ports used by the components.
        child_servers (list[HvHostDiscoveryModel] | Unset): Array of Microsoft Hyper-V hosts.
        parent_host_id (UUID | Unset): Parent host ID.
        parent_host_name (str | Unset): Parent host name.
    """

    id: UUID
    name: str
    description: str
    type_: EManagedServerType
    status: EManagedServersStatus
    credentials_id: UUID
    network_settings: ManagedHostNetworkSettingsModel | Unset = UNSET
    child_servers: list[HvHostDiscoveryModel] | Unset = UNSET
    parent_host_id: UUID | Unset = UNSET
    parent_host_name: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        description = self.description

        type_ = self.type_.value

        status = self.status.value

        credentials_id = str(self.credentials_id)

        network_settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.network_settings, Unset):
            network_settings = self.network_settings.to_dict()

        child_servers: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.child_servers, Unset):
            child_servers = []
            for child_servers_item_data in self.child_servers:
                child_servers_item = child_servers_item_data.to_dict()
                child_servers.append(child_servers_item)

        parent_host_id: str | Unset = UNSET
        if not isinstance(self.parent_host_id, Unset):
            parent_host_id = str(self.parent_host_id)

        parent_host_name = self.parent_host_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "description": description,
                "type": type_,
                "status": status,
                "credentialsId": credentials_id,
            }
        )
        if network_settings is not UNSET:
            field_dict["networkSettings"] = network_settings
        if child_servers is not UNSET:
            field_dict["childServers"] = child_servers
        if parent_host_id is not UNSET:
            field_dict["parentHostId"] = parent_host_id
        if parent_host_name is not UNSET:
            field_dict["parentHostName"] = parent_host_name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.hv_host_discovery_model import HvHostDiscoveryModel
        from ..models.managed_host_network_settings_model import ManagedHostNetworkSettingsModel

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        description = d.pop("description")

        type_ = EManagedServerType(d.pop("type"))

        status = EManagedServersStatus(d.pop("status"))

        credentials_id = UUID(d.pop("credentialsId"))

        _network_settings = d.pop("networkSettings", UNSET)
        network_settings: ManagedHostNetworkSettingsModel | Unset
        if isinstance(_network_settings, Unset):
            network_settings = UNSET
        else:
            network_settings = ManagedHostNetworkSettingsModel.from_dict(_network_settings)

        _child_servers = d.pop("childServers", UNSET)
        child_servers: list[HvHostDiscoveryModel] | Unset = UNSET
        if _child_servers is not UNSET:
            child_servers = []
            for child_servers_item_data in _child_servers:
                child_servers_item = HvHostDiscoveryModel.from_dict(child_servers_item_data)

                child_servers.append(child_servers_item)

        _parent_host_id = d.pop("parentHostId", UNSET)
        parent_host_id: UUID | Unset
        if isinstance(_parent_host_id, Unset):
            parent_host_id = UNSET
        else:
            parent_host_id = UUID(_parent_host_id)

        parent_host_name = d.pop("parentHostName", UNSET)

        hv_host_cluster_model = cls(
            id=id,
            name=name,
            description=description,
            type_=type_,
            status=status,
            credentials_id=credentials_id,
            network_settings=network_settings,
            child_servers=child_servers,
            parent_host_id=parent_host_id,
            parent_host_name=parent_host_name,
        )

        hv_host_cluster_model.additional_properties = d
        return hv_host_cluster_model

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
