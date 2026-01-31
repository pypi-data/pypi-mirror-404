from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_backup_proxy_transport_mode import EBackupProxyTransportMode
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.proxy_datastore_settings_model import ProxyDatastoreSettingsModel


T = TypeVar("T", bound="ProxyServerSettingsModel")


@_attrs_define
class ProxyServerSettingsModel:
    """Server settings for the backup proxy.

    Attributes:
        host_id (UUID): ID of the server.
        transport_mode (EBackupProxyTransportMode | Unset): Transport mode of the backup proxy.
        failover_to_network (bool | Unset): (For the Direct storage access and Virtual appliance transport modes) If
            `true`, Veeam Backup & Replication failovers to the network transport mode in case the primary mode fails or is
            unavailable.
        host_to_proxy_encryption (bool | Unset): (For the Network mode) If `true`, VM data is transferred over an
            encrypted TLS connection.
        connected_datastores (ProxyDatastoreSettingsModel | Unset): Datastores to which the backup proxy has a direct
            SAN or NFS connection.
        max_task_count (int | Unset): Maximum number of concurrent tasks.
    """

    host_id: UUID
    transport_mode: EBackupProxyTransportMode | Unset = UNSET
    failover_to_network: bool | Unset = UNSET
    host_to_proxy_encryption: bool | Unset = UNSET
    connected_datastores: ProxyDatastoreSettingsModel | Unset = UNSET
    max_task_count: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        host_id = str(self.host_id)

        transport_mode: str | Unset = UNSET
        if not isinstance(self.transport_mode, Unset):
            transport_mode = self.transport_mode.value

        failover_to_network = self.failover_to_network

        host_to_proxy_encryption = self.host_to_proxy_encryption

        connected_datastores: dict[str, Any] | Unset = UNSET
        if not isinstance(self.connected_datastores, Unset):
            connected_datastores = self.connected_datastores.to_dict()

        max_task_count = self.max_task_count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "hostId": host_id,
            }
        )
        if transport_mode is not UNSET:
            field_dict["transportMode"] = transport_mode
        if failover_to_network is not UNSET:
            field_dict["failoverToNetwork"] = failover_to_network
        if host_to_proxy_encryption is not UNSET:
            field_dict["hostToProxyEncryption"] = host_to_proxy_encryption
        if connected_datastores is not UNSET:
            field_dict["connectedDatastores"] = connected_datastores
        if max_task_count is not UNSET:
            field_dict["maxTaskCount"] = max_task_count

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.proxy_datastore_settings_model import ProxyDatastoreSettingsModel

        d = dict(src_dict)
        host_id = UUID(d.pop("hostId"))

        _transport_mode = d.pop("transportMode", UNSET)
        transport_mode: EBackupProxyTransportMode | Unset
        if isinstance(_transport_mode, Unset):
            transport_mode = UNSET
        else:
            transport_mode = EBackupProxyTransportMode(_transport_mode)

        failover_to_network = d.pop("failoverToNetwork", UNSET)

        host_to_proxy_encryption = d.pop("hostToProxyEncryption", UNSET)

        _connected_datastores = d.pop("connectedDatastores", UNSET)
        connected_datastores: ProxyDatastoreSettingsModel | Unset
        if isinstance(_connected_datastores, Unset):
            connected_datastores = UNSET
        else:
            connected_datastores = ProxyDatastoreSettingsModel.from_dict(_connected_datastores)

        max_task_count = d.pop("maxTaskCount", UNSET)

        proxy_server_settings_model = cls(
            host_id=host_id,
            transport_mode=transport_mode,
            failover_to_network=failover_to_network,
            host_to_proxy_encryption=host_to_proxy_encryption,
            connected_datastores=connected_datastores,
            max_task_count=max_task_count,
        )

        proxy_server_settings_model.additional_properties = d
        return proxy_server_settings_model

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
