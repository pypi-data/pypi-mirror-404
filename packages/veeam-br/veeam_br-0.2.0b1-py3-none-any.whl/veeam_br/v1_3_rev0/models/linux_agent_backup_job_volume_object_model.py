from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_linux_volume_type import ELinuxVolumeType

T = TypeVar("T", bound="LinuxAgentBackupJobVolumeObjectModel")


@_attrs_define
class LinuxAgentBackupJobVolumeObjectModel:
    """Volume object.

    Attributes:
        path (str): Path to the volume object.
        type_ (ELinuxVolumeType): Volume type of the Linux machine.
    """

    path: str
    type_: ELinuxVolumeType
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        path = self.path

        type_ = self.type_.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "path": path,
                "type": type_,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        path = d.pop("path")

        type_ = ELinuxVolumeType(d.pop("type"))

        linux_agent_backup_job_volume_object_model = cls(
            path=path,
            type_=type_,
        )

        linux_agent_backup_job_volume_object_model.additional_properties = d
        return linux_agent_backup_job_volume_object_model

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
