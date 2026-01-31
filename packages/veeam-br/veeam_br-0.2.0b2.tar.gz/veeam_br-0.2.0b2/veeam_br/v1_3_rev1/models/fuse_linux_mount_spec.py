from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_credentials_storage_type import ECredentialsStorageType
from ..models.e_publish_backup_content_mode_type import EPublishBackupContentModeType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.linux_credentials_spec import LinuxCredentialsSpec
    from ..models.linux_host_ssh_settings_model import LinuxHostSSHSettingsModel


T = TypeVar("T", bound="FUSELinuxMountSpec")


@_attrs_define
class FUSELinuxMountSpec:
    """FUSE mount settings. If you use the `SingleUse` credentials type, you must specify credentials in the
    `singleUseSSHCredentials` property.

        Attributes:
            restore_point_id (UUID): Restore point ID. You can use restore points from backups and snapshot replicas.
            type_ (EPublishBackupContentModeType): Disk publishing mount mode.<ul><li>ISCSITarget — Automatic iSCSI mode.
                Use this mode if you want Veeam Backup & Replication to automatically configure the iSCSI initiator, start an
                iSCSI session and allow the specified target Microsoft Windows server to access disk content.</li>
                <li>ISCSIWindowsMount — Manual iSCSI mode. Use this mode if you want to manually start an iSCSI session from any
                Microsoft Windows server that has access to the iSCSI target server (mount server).</li> <li>FUSELinuxMount —
                FUSE mode. Use this mode to allow the specified target Linux or Unix server to access disk content.</li></ul>
            target_server_name (str): DNS name or IP address of the target server.
            credentials_storage_type (ECredentialsStorageType): Credentials type used to connect to the server.
            disk_names (list[str] | Unset): Array of disk names.
            reason (str | Unset): Reason for publishing the backup.
            target_server_credentials_id (UUID | Unset): Credentials ID of the target server.
            single_use_ssh_credentials (LinuxCredentialsSpec | Unset): Settings for single-use credentials.
            ssh_settings (LinuxHostSSHSettingsModel | Unset): SSH settings of the Linux host.
            mount_host_id (UUID | Unset): Mount server ID.
    """

    restore_point_id: UUID
    type_: EPublishBackupContentModeType
    target_server_name: str
    credentials_storage_type: ECredentialsStorageType
    disk_names: list[str] | Unset = UNSET
    reason: str | Unset = UNSET
    target_server_credentials_id: UUID | Unset = UNSET
    single_use_ssh_credentials: LinuxCredentialsSpec | Unset = UNSET
    ssh_settings: LinuxHostSSHSettingsModel | Unset = UNSET
    mount_host_id: UUID | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        restore_point_id = str(self.restore_point_id)

        type_ = self.type_.value

        target_server_name = self.target_server_name

        credentials_storage_type = self.credentials_storage_type.value

        disk_names: list[str] | Unset = UNSET
        if not isinstance(self.disk_names, Unset):
            disk_names = self.disk_names

        reason = self.reason

        target_server_credentials_id: str | Unset = UNSET
        if not isinstance(self.target_server_credentials_id, Unset):
            target_server_credentials_id = str(self.target_server_credentials_id)

        single_use_ssh_credentials: dict[str, Any] | Unset = UNSET
        if not isinstance(self.single_use_ssh_credentials, Unset):
            single_use_ssh_credentials = self.single_use_ssh_credentials.to_dict()

        ssh_settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.ssh_settings, Unset):
            ssh_settings = self.ssh_settings.to_dict()

        mount_host_id: str | Unset = UNSET
        if not isinstance(self.mount_host_id, Unset):
            mount_host_id = str(self.mount_host_id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "restorePointId": restore_point_id,
                "type": type_,
                "targetServerName": target_server_name,
                "credentialsStorageType": credentials_storage_type,
            }
        )
        if disk_names is not UNSET:
            field_dict["diskNames"] = disk_names
        if reason is not UNSET:
            field_dict["reason"] = reason
        if target_server_credentials_id is not UNSET:
            field_dict["targetServerCredentialsId"] = target_server_credentials_id
        if single_use_ssh_credentials is not UNSET:
            field_dict["singleUseSSHCredentials"] = single_use_ssh_credentials
        if ssh_settings is not UNSET:
            field_dict["sshSettings"] = ssh_settings
        if mount_host_id is not UNSET:
            field_dict["mountHostId"] = mount_host_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.linux_credentials_spec import LinuxCredentialsSpec
        from ..models.linux_host_ssh_settings_model import LinuxHostSSHSettingsModel

        d = dict(src_dict)
        restore_point_id = UUID(d.pop("restorePointId"))

        type_ = EPublishBackupContentModeType(d.pop("type"))

        target_server_name = d.pop("targetServerName")

        credentials_storage_type = ECredentialsStorageType(d.pop("credentialsStorageType"))

        disk_names = cast(list[str], d.pop("diskNames", UNSET))

        reason = d.pop("reason", UNSET)

        _target_server_credentials_id = d.pop("targetServerCredentialsId", UNSET)
        target_server_credentials_id: UUID | Unset
        if isinstance(_target_server_credentials_id, Unset):
            target_server_credentials_id = UNSET
        else:
            target_server_credentials_id = UUID(_target_server_credentials_id)

        _single_use_ssh_credentials = d.pop("singleUseSSHCredentials", UNSET)
        single_use_ssh_credentials: LinuxCredentialsSpec | Unset
        if isinstance(_single_use_ssh_credentials, Unset):
            single_use_ssh_credentials = UNSET
        else:
            single_use_ssh_credentials = LinuxCredentialsSpec.from_dict(_single_use_ssh_credentials)

        _ssh_settings = d.pop("sshSettings", UNSET)
        ssh_settings: LinuxHostSSHSettingsModel | Unset
        if isinstance(_ssh_settings, Unset):
            ssh_settings = UNSET
        else:
            ssh_settings = LinuxHostSSHSettingsModel.from_dict(_ssh_settings)

        _mount_host_id = d.pop("mountHostId", UNSET)
        mount_host_id: UUID | Unset
        if isinstance(_mount_host_id, Unset):
            mount_host_id = UNSET
        else:
            mount_host_id = UUID(_mount_host_id)

        fuse_linux_mount_spec = cls(
            restore_point_id=restore_point_id,
            type_=type_,
            target_server_name=target_server_name,
            credentials_storage_type=credentials_storage_type,
            disk_names=disk_names,
            reason=reason,
            target_server_credentials_id=target_server_credentials_id,
            single_use_ssh_credentials=single_use_ssh_credentials,
            ssh_settings=ssh_settings,
            mount_host_id=mount_host_id,
        )

        fuse_linux_mount_spec.additional_properties = d
        return fuse_linux_mount_spec

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
