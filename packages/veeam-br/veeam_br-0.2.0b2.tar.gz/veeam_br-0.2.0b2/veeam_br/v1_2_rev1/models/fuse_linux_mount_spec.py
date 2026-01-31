from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_publish_backup_content_mode_type import EPublishBackupContentModeType
from ..types import UNSET, Unset

T = TypeVar("T", bound="FUSELinuxMountSpec")


@_attrs_define
class FUSELinuxMountSpec:
    """
    Attributes:
        restore_point_id (UUID): Restore point ID. You can use restore points from backups and snapshot replicas.
        type_ (EPublishBackupContentModeType): Disk publishing mount mode.<ul><li>ISCSITarget — Automatic iSCSI mode.
            Use this mode if you want Veeam Backup & Replication to automatically configure the iSCSI initiator, start an
            iSCSI session and allow the specified target Microsoft Windows server to access disk content.</li>
            <li>ISCSIWindowsMount — Manual iSCSI mode. Use this mode if you want to manually start an iSCSI session from any
            Microsoft Windows server that has access to the iSCSI target server (mount server).</li> <li>FUSELinuxMount —
            FUSE mode. Use this mode to allow the specified target Linux or Unix server to access disk content.</li></ul>
        target_server_name (str): DNS name or IP address of the target server.
        target_server_credentials_id (UUID): Credentials ID of the target server.
        disk_names (list[str] | Unset): Array of disk names.
        mount_host_id (UUID | Unset): Mount server ID.
    """

    restore_point_id: UUID
    type_: EPublishBackupContentModeType
    target_server_name: str
    target_server_credentials_id: UUID
    disk_names: list[str] | Unset = UNSET
    mount_host_id: UUID | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        restore_point_id = str(self.restore_point_id)

        type_ = self.type_.value

        target_server_name = self.target_server_name

        target_server_credentials_id = str(self.target_server_credentials_id)

        disk_names: list[str] | Unset = UNSET
        if not isinstance(self.disk_names, Unset):
            disk_names = self.disk_names

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
                "targetServerCredentialsId": target_server_credentials_id,
            }
        )
        if disk_names is not UNSET:
            field_dict["diskNames"] = disk_names
        if mount_host_id is not UNSET:
            field_dict["mountHostId"] = mount_host_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        restore_point_id = UUID(d.pop("restorePointId"))

        type_ = EPublishBackupContentModeType(d.pop("type"))

        target_server_name = d.pop("targetServerName")

        target_server_credentials_id = UUID(d.pop("targetServerCredentialsId"))

        disk_names = cast(list[str], d.pop("diskNames", UNSET))

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
            target_server_credentials_id=target_server_credentials_id,
            disk_names=disk_names,
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
