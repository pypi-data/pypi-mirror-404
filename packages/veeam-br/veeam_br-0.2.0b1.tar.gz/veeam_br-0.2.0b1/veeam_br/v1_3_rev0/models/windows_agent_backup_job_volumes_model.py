from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_agent_volumes_backup_mode import EAgentVolumesBackupMode

if TYPE_CHECKING:
    from ..models.windows_agent_backup_job_volume_object_model import WindowsAgentBackupJobVolumeObjectModel


T = TypeVar("T", bound="WindowsAgentBackupJobVolumesModel")


@_attrs_define
class WindowsAgentBackupJobVolumesModel:
    """Scope of volumes protected by the Veeam Agent for Windows backup job.

    Attributes:
        volumes_backup_mode (EAgentVolumesBackupMode): Backup mode for volume of protected machine.
        volume_object (list[WindowsAgentBackupJobVolumeObjectModel]): Array of volume objects.
    """

    volumes_backup_mode: EAgentVolumesBackupMode
    volume_object: list[WindowsAgentBackupJobVolumeObjectModel]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        volumes_backup_mode = self.volumes_backup_mode.value

        volume_object = []
        for volume_object_item_data in self.volume_object:
            volume_object_item = volume_object_item_data.to_dict()
            volume_object.append(volume_object_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "volumesBackupMode": volumes_backup_mode,
                "volumeObject": volume_object,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.windows_agent_backup_job_volume_object_model import WindowsAgentBackupJobVolumeObjectModel

        d = dict(src_dict)
        volumes_backup_mode = EAgentVolumesBackupMode(d.pop("volumesBackupMode"))

        volume_object = []
        _volume_object = d.pop("volumeObject")
        for volume_object_item_data in _volume_object:
            volume_object_item = WindowsAgentBackupJobVolumeObjectModel.from_dict(volume_object_item_data)

            volume_object.append(volume_object_item)

        windows_agent_backup_job_volumes_model = cls(
            volumes_backup_mode=volumes_backup_mode,
            volume_object=volume_object,
        )

        windows_agent_backup_job_volumes_model.additional_properties = d
        return windows_agent_backup_job_volumes_model

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
