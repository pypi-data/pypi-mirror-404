from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_windows_volume_type import EWindowsVolumeType
from ..types import UNSET, Unset

T = TypeVar("T", bound="WindowsAgentBackupJobVolumeObjectModel")


@_attrs_define
class WindowsAgentBackupJobVolumeObjectModel:
    """Volume object.

    Attributes:
        type_ (EWindowsVolumeType): Volume type of the Windows machine.
        path (str | Unset): Path to the volume object.
    """

    type_: EWindowsVolumeType
    path: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        path = self.path

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
            }
        )
        if path is not UNSET:
            field_dict["path"] = path

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        type_ = EWindowsVolumeType(d.pop("type"))

        path = d.pop("path", UNSET)

        windows_agent_backup_job_volume_object_model = cls(
            type_=type_,
            path=path,
        )

        windows_agent_backup_job_volume_object_model.additional_properties = d
        return windows_agent_backup_job_volume_object_model

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
