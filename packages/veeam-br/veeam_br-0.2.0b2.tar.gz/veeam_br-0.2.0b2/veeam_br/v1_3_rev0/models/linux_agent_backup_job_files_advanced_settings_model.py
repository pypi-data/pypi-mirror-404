from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="LinuxAgentBackupJobFilesAdvancedSettingsModel")


@_attrs_define
class LinuxAgentBackupJobFilesAdvancedSettingsModel:
    """Advanced settings for files backed up with Veeam Agent for Linux backup job.

    Attributes:
        include_masks (list[str] | Unset): Array of file names and/or masks for file types that you want to include into
            the backup scope.
        exclude_masks (list[str] | Unset): Array of file names and/or masks for file types that you want to exclude from
            the backup scope.
    """

    include_masks: list[str] | Unset = UNSET
    exclude_masks: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        include_masks: list[str] | Unset = UNSET
        if not isinstance(self.include_masks, Unset):
            include_masks = self.include_masks

        exclude_masks: list[str] | Unset = UNSET
        if not isinstance(self.exclude_masks, Unset):
            exclude_masks = self.exclude_masks

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if include_masks is not UNSET:
            field_dict["includeMasks"] = include_masks
        if exclude_masks is not UNSET:
            field_dict["excludeMasks"] = exclude_masks

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        include_masks = cast(list[str], d.pop("includeMasks", UNSET))

        exclude_masks = cast(list[str], d.pop("excludeMasks", UNSET))

        linux_agent_backup_job_files_advanced_settings_model = cls(
            include_masks=include_masks,
            exclude_masks=exclude_masks,
        )

        linux_agent_backup_job_files_advanced_settings_model.additional_properties = d
        return linux_agent_backup_job_files_advanced_settings_model

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
