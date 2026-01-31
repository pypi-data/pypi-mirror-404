from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_credentials_storage_type import ECredentialsStorageType
from ..models.e_host_updates_state import EHostUpdatesState
from ..models.e_managed_server_type import EManagedServerType
from ..models.e_managed_servers_status import EManagedServersStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.managed_host_ports_model import ManagedHostPortsModel


T = TypeVar("T", bound="WindowsHostModel")


@_attrs_define
class WindowsHostModel:
    """Microsoft Windows server.

    Attributes:
        id (UUID): ID of the server.
        name (str): Full DNS name or IP address of the server.
        description (str): Description of the server.
        type_ (EManagedServerType): Type of the server.
        status (EManagedServersStatus): Availability status.
        credentials_storage_type (ECredentialsStorageType): Credentials type used to connect to the server.
        credentials_id (UUID | Unset): ID of the credentials used to connect to the server.
        network_settings (ManagedHostPortsModel | Unset): Veeam Backup & Replication components installed on the server
            and ports used by the components.
        is_backup_server (bool | Unset): If `true`, the Microsoft Windows server is a backup server.
        is_default_mount_server (bool | Unset): If `true`, the server is the default mount server for Microsoft Windows
            machines.
        updates_state (EHostUpdatesState | Unset): Host updates state.
    """

    id: UUID
    name: str
    description: str
    type_: EManagedServerType
    status: EManagedServersStatus
    credentials_storage_type: ECredentialsStorageType
    credentials_id: UUID | Unset = UNSET
    network_settings: ManagedHostPortsModel | Unset = UNSET
    is_backup_server: bool | Unset = UNSET
    is_default_mount_server: bool | Unset = UNSET
    updates_state: EHostUpdatesState | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        description = self.description

        type_ = self.type_.value

        status = self.status.value

        credentials_storage_type = self.credentials_storage_type.value

        credentials_id: str | Unset = UNSET
        if not isinstance(self.credentials_id, Unset):
            credentials_id = str(self.credentials_id)

        network_settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.network_settings, Unset):
            network_settings = self.network_settings.to_dict()

        is_backup_server = self.is_backup_server

        is_default_mount_server = self.is_default_mount_server

        updates_state: str | Unset = UNSET
        if not isinstance(self.updates_state, Unset):
            updates_state = self.updates_state.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "description": description,
                "type": type_,
                "status": status,
                "credentialsStorageType": credentials_storage_type,
            }
        )
        if credentials_id is not UNSET:
            field_dict["credentialsId"] = credentials_id
        if network_settings is not UNSET:
            field_dict["networkSettings"] = network_settings
        if is_backup_server is not UNSET:
            field_dict["isBackupServer"] = is_backup_server
        if is_default_mount_server is not UNSET:
            field_dict["isDefaultMountServer"] = is_default_mount_server
        if updates_state is not UNSET:
            field_dict["updatesState"] = updates_state

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.managed_host_ports_model import ManagedHostPortsModel

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        description = d.pop("description")

        type_ = EManagedServerType(d.pop("type"))

        status = EManagedServersStatus(d.pop("status"))

        credentials_storage_type = ECredentialsStorageType(d.pop("credentialsStorageType"))

        _credentials_id = d.pop("credentialsId", UNSET)
        credentials_id: UUID | Unset
        if isinstance(_credentials_id, Unset):
            credentials_id = UNSET
        else:
            credentials_id = UUID(_credentials_id)

        _network_settings = d.pop("networkSettings", UNSET)
        network_settings: ManagedHostPortsModel | Unset
        if isinstance(_network_settings, Unset):
            network_settings = UNSET
        else:
            network_settings = ManagedHostPortsModel.from_dict(_network_settings)

        is_backup_server = d.pop("isBackupServer", UNSET)

        is_default_mount_server = d.pop("isDefaultMountServer", UNSET)

        _updates_state = d.pop("updatesState", UNSET)
        updates_state: EHostUpdatesState | Unset
        if isinstance(_updates_state, Unset):
            updates_state = UNSET
        else:
            updates_state = EHostUpdatesState(_updates_state)

        windows_host_model = cls(
            id=id,
            name=name,
            description=description,
            type_=type_,
            status=status,
            credentials_storage_type=credentials_storage_type,
            credentials_id=credentials_id,
            network_settings=network_settings,
            is_backup_server=is_backup_server,
            is_default_mount_server=is_default_mount_server,
            updates_state=updates_state,
        )

        windows_host_model.additional_properties = d
        return windows_host_model

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
