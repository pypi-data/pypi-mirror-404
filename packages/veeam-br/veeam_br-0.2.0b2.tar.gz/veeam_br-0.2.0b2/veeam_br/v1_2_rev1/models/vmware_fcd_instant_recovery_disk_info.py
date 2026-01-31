from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="VmwareFcdInstantRecoveryDiskInfo")


@_attrs_define
class VmwareFcdInstantRecoveryDiskInfo:
    """
    Attributes:
        name_in_backup (str): Disk name displayed in the backup.
        mounted_disk_name (str): Name of the VMDK file that is stored in the datastore.
        registered_fcd_name (str): Name under which the disk is registered as an FCD in the vCenter Managed Object
            Browser.
        object_id (str): FCD ID.
    """

    name_in_backup: str
    mounted_disk_name: str
    registered_fcd_name: str
    object_id: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name_in_backup = self.name_in_backup

        mounted_disk_name = self.mounted_disk_name

        registered_fcd_name = self.registered_fcd_name

        object_id = self.object_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "nameInBackup": name_in_backup,
                "mountedDiskName": mounted_disk_name,
                "registeredFcdName": registered_fcd_name,
                "objectId": object_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name_in_backup = d.pop("nameInBackup")

        mounted_disk_name = d.pop("mountedDiskName")

        registered_fcd_name = d.pop("registeredFcdName")

        object_id = d.pop("objectId")

        vmware_fcd_instant_recovery_disk_info = cls(
            name_in_backup=name_in_backup,
            mounted_disk_name=mounted_disk_name,
            registered_fcd_name=registered_fcd_name,
            object_id=object_id,
        )

        vmware_fcd_instant_recovery_disk_info.additional_properties = d
        return vmware_fcd_instant_recovery_disk_info

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
