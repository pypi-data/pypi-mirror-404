from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_backup_content_disk_publish_mode import EBackupContentDiskPublishMode
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.backup_content_disk_publication_info import BackupContentDiskPublicationInfo


T = TypeVar("T", bound="BackupContentPublicationInfo")


@_attrs_define
class BackupContentPublicationInfo:
    """Details about the publishing operation.

    Attributes:
        mode (EBackupContentDiskPublishMode | Unset): Disk publishing mount mode.
        server_port (int | Unset): Port used by the mount point.
        server_ips (list[str] | Unset): Array of target server IP addresses.
        disks (list[BackupContentDiskPublicationInfo] | Unset): Array of objects containing details about the published
            disks.
    """

    mode: EBackupContentDiskPublishMode | Unset = UNSET
    server_port: int | Unset = UNSET
    server_ips: list[str] | Unset = UNSET
    disks: list[BackupContentDiskPublicationInfo] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        mode: str | Unset = UNSET
        if not isinstance(self.mode, Unset):
            mode = self.mode.value

        server_port = self.server_port

        server_ips: list[str] | Unset = UNSET
        if not isinstance(self.server_ips, Unset):
            server_ips = self.server_ips

        disks: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.disks, Unset):
            disks = []
            for disks_item_data in self.disks:
                disks_item = disks_item_data.to_dict()
                disks.append(disks_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if mode is not UNSET:
            field_dict["mode"] = mode
        if server_port is not UNSET:
            field_dict["serverPort"] = server_port
        if server_ips is not UNSET:
            field_dict["serverIps"] = server_ips
        if disks is not UNSET:
            field_dict["disks"] = disks

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.backup_content_disk_publication_info import BackupContentDiskPublicationInfo

        d = dict(src_dict)
        _mode = d.pop("mode", UNSET)
        mode: EBackupContentDiskPublishMode | Unset
        if isinstance(_mode, Unset):
            mode = UNSET
        else:
            mode = EBackupContentDiskPublishMode(_mode)

        server_port = d.pop("serverPort", UNSET)

        server_ips = cast(list[str], d.pop("serverIps", UNSET))

        _disks = d.pop("disks", UNSET)
        disks: list[BackupContentDiskPublicationInfo] | Unset = UNSET
        if _disks is not UNSET:
            disks = []
            for disks_item_data in _disks:
                disks_item = BackupContentDiskPublicationInfo.from_dict(disks_item_data)

                disks.append(disks_item)

        backup_content_publication_info = cls(
            mode=mode,
            server_port=server_port,
            server_ips=server_ips,
            disks=disks,
        )

        backup_content_publication_info.additional_properties = d
        return backup_content_publication_info

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
