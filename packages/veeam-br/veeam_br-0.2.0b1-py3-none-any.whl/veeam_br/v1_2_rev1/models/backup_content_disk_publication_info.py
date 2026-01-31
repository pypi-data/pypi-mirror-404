from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="BackupContentDiskPublicationInfo")


@_attrs_define
class BackupContentDiskPublicationInfo:
    """Details about a published disk.

    Attributes:
        disk_id (str | Unset): Disk ID.
        disk_name (str | Unset): The path of the published disk.
        access_link (str | Unset): iSCSI Qualified Name (IQN) of the disk. Only available for the iSCSI mount mode.
        mount_points (list[str] | Unset): Array of mount point paths.
    """

    disk_id: str | Unset = UNSET
    disk_name: str | Unset = UNSET
    access_link: str | Unset = UNSET
    mount_points: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        disk_id = self.disk_id

        disk_name = self.disk_name

        access_link = self.access_link

        mount_points: list[str] | Unset = UNSET
        if not isinstance(self.mount_points, Unset):
            mount_points = self.mount_points

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if disk_id is not UNSET:
            field_dict["diskId"] = disk_id
        if disk_name is not UNSET:
            field_dict["diskName"] = disk_name
        if access_link is not UNSET:
            field_dict["accessLink"] = access_link
        if mount_points is not UNSET:
            field_dict["mountPoints"] = mount_points

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        disk_id = d.pop("diskId", UNSET)

        disk_name = d.pop("diskName", UNSET)

        access_link = d.pop("accessLink", UNSET)

        mount_points = cast(list[str], d.pop("mountPoints", UNSET))

        backup_content_disk_publication_info = cls(
            disk_id=disk_id,
            disk_name=disk_name,
            access_link=access_link,
            mount_points=mount_points,
        )

        backup_content_disk_publication_info.additional_properties = d
        return backup_content_disk_publication_info

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
