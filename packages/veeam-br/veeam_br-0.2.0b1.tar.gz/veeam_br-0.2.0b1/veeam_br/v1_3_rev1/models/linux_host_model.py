from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.e_credentials_storage_type import ECredentialsStorageType
from ..models.e_host_updates_state import EHostUpdatesState
from ..models.e_managed_server_type import EManagedServerType
from ..models.e_managed_servers_status import EManagedServersStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.host_optional_components import HostOptionalComponents
    from ..models.linux_credentials_spec import LinuxCredentialsSpec
    from ..models.linux_host_ssh_settings_model import LinuxHostSSHSettingsModel


T = TypeVar("T", bound="LinuxHostModel")


@_attrs_define
class LinuxHostModel:
    """Linux server.

    Attributes:
        id (UUID): ID of the server.
        name (str): Full DNS name or IP address of the server.
        description (str): Description of the server.
        type_ (EManagedServerType): Type of the server.
        status (EManagedServersStatus): Availability status.
        credentials_storage_type (ECredentialsStorageType): Credentials type used to connect to the server.
        credentials_id (UUID | Unset): Permanent credentials ID.
        single_use_credentials (LinuxCredentialsSpec | Unset): Settings for single-use credentials.
        ssh_settings (LinuxHostSSHSettingsModel | Unset): SSH settings of the Linux host.
        is_backup_server (bool | Unset): If `true`, the Linux server is a backup server.
        updates_state (EHostUpdatesState | Unset): Host updates state.
        auto_update_deadline (datetime.datetime | Unset): Date and time when the update will be automatically installed.
        is_default_mount_server (bool | Unset): If `true`, the Linux server is the default mount server for Linux
            machines.
        handshake_code (str | Unset): Handshake code to create pairing with Veeam Backup & Replication.
        optional_components (HostOptionalComponents | Unset): Optional components to be installed on the server.
        is_vbr_linux_appliance (bool | Unset): If `true`, the Linux server is a backup server.
    """

    id: UUID
    name: str
    description: str
    type_: EManagedServerType
    status: EManagedServersStatus
    credentials_storage_type: ECredentialsStorageType
    credentials_id: UUID | Unset = UNSET
    single_use_credentials: LinuxCredentialsSpec | Unset = UNSET
    ssh_settings: LinuxHostSSHSettingsModel | Unset = UNSET
    is_backup_server: bool | Unset = UNSET
    updates_state: EHostUpdatesState | Unset = UNSET
    auto_update_deadline: datetime.datetime | Unset = UNSET
    is_default_mount_server: bool | Unset = UNSET
    handshake_code: str | Unset = UNSET
    optional_components: HostOptionalComponents | Unset = UNSET
    is_vbr_linux_appliance: bool | Unset = UNSET
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

        single_use_credentials: dict[str, Any] | Unset = UNSET
        if not isinstance(self.single_use_credentials, Unset):
            single_use_credentials = self.single_use_credentials.to_dict()

        ssh_settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.ssh_settings, Unset):
            ssh_settings = self.ssh_settings.to_dict()

        is_backup_server = self.is_backup_server

        updates_state: str | Unset = UNSET
        if not isinstance(self.updates_state, Unset):
            updates_state = self.updates_state.value

        auto_update_deadline: str | Unset = UNSET
        if not isinstance(self.auto_update_deadline, Unset):
            auto_update_deadline = self.auto_update_deadline.isoformat()

        is_default_mount_server = self.is_default_mount_server

        handshake_code = self.handshake_code

        optional_components: dict[str, Any] | Unset = UNSET
        if not isinstance(self.optional_components, Unset):
            optional_components = self.optional_components.to_dict()

        is_vbr_linux_appliance = self.is_vbr_linux_appliance

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
        if single_use_credentials is not UNSET:
            field_dict["singleUseCredentials"] = single_use_credentials
        if ssh_settings is not UNSET:
            field_dict["sshSettings"] = ssh_settings
        if is_backup_server is not UNSET:
            field_dict["isBackupServer"] = is_backup_server
        if updates_state is not UNSET:
            field_dict["updatesState"] = updates_state
        if auto_update_deadline is not UNSET:
            field_dict["autoUpdateDeadline"] = auto_update_deadline
        if is_default_mount_server is not UNSET:
            field_dict["isDefaultMountServer"] = is_default_mount_server
        if handshake_code is not UNSET:
            field_dict["handshakeCode"] = handshake_code
        if optional_components is not UNSET:
            field_dict["optionalComponents"] = optional_components
        if is_vbr_linux_appliance is not UNSET:
            field_dict["isVBRLinuxAppliance"] = is_vbr_linux_appliance

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.host_optional_components import HostOptionalComponents
        from ..models.linux_credentials_spec import LinuxCredentialsSpec
        from ..models.linux_host_ssh_settings_model import LinuxHostSSHSettingsModel

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

        _single_use_credentials = d.pop("singleUseCredentials", UNSET)
        single_use_credentials: LinuxCredentialsSpec | Unset
        if isinstance(_single_use_credentials, Unset):
            single_use_credentials = UNSET
        else:
            single_use_credentials = LinuxCredentialsSpec.from_dict(_single_use_credentials)

        _ssh_settings = d.pop("sshSettings", UNSET)
        ssh_settings: LinuxHostSSHSettingsModel | Unset
        if isinstance(_ssh_settings, Unset):
            ssh_settings = UNSET
        else:
            ssh_settings = LinuxHostSSHSettingsModel.from_dict(_ssh_settings)

        is_backup_server = d.pop("isBackupServer", UNSET)

        _updates_state = d.pop("updatesState", UNSET)
        updates_state: EHostUpdatesState | Unset
        if isinstance(_updates_state, Unset):
            updates_state = UNSET
        else:
            updates_state = EHostUpdatesState(_updates_state)

        _auto_update_deadline = d.pop("autoUpdateDeadline", UNSET)
        auto_update_deadline: datetime.datetime | Unset
        if isinstance(_auto_update_deadline, Unset):
            auto_update_deadline = UNSET
        else:
            auto_update_deadline = isoparse(_auto_update_deadline)

        is_default_mount_server = d.pop("isDefaultMountServer", UNSET)

        handshake_code = d.pop("handshakeCode", UNSET)

        _optional_components = d.pop("optionalComponents", UNSET)
        optional_components: HostOptionalComponents | Unset
        if isinstance(_optional_components, Unset):
            optional_components = UNSET
        else:
            optional_components = HostOptionalComponents.from_dict(_optional_components)

        is_vbr_linux_appliance = d.pop("isVBRLinuxAppliance", UNSET)

        linux_host_model = cls(
            id=id,
            name=name,
            description=description,
            type_=type_,
            status=status,
            credentials_storage_type=credentials_storage_type,
            credentials_id=credentials_id,
            single_use_credentials=single_use_credentials,
            ssh_settings=ssh_settings,
            is_backup_server=is_backup_server,
            updates_state=updates_state,
            auto_update_deadline=auto_update_deadline,
            is_default_mount_server=is_default_mount_server,
            handshake_code=handshake_code,
            optional_components=optional_components,
            is_vbr_linux_appliance=is_vbr_linux_appliance,
        )

        linux_host_model.additional_properties = d
        return linux_host_model

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
