from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.linux_agent_backup_job_volume_object_model import LinuxAgentBackupJobVolumeObjectModel


T = TypeVar("T", bound="LinuxAgentBackupJobVolumesModel")


@_attrs_define
class LinuxAgentBackupJobVolumesModel:
    """Details on volume objects.

    Attributes:
        volume_object (list[LinuxAgentBackupJobVolumeObjectModel]): Array of volume objects.
    """

    volume_object: list[LinuxAgentBackupJobVolumeObjectModel]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        volume_object = []
        for volume_object_item_data in self.volume_object:
            volume_object_item = volume_object_item_data.to_dict()
            volume_object.append(volume_object_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "volumeObject": volume_object,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.linux_agent_backup_job_volume_object_model import LinuxAgentBackupJobVolumeObjectModel

        d = dict(src_dict)
        volume_object = []
        _volume_object = d.pop("volumeObject")
        for volume_object_item_data in _volume_object:
            volume_object_item = LinuxAgentBackupJobVolumeObjectModel.from_dict(volume_object_item_data)

            volume_object.append(volume_object_item)

        linux_agent_backup_job_volumes_model = cls(
            volume_object=volume_object,
        )

        linux_agent_backup_job_volumes_model.additional_properties = d
        return linux_agent_backup_job_volumes_model

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
