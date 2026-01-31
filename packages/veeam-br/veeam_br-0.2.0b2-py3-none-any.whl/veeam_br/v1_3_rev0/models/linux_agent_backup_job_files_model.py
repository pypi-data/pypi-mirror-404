from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.linux_agent_backup_job_files_advanced_settings_model import (
        LinuxAgentBackupJobFilesAdvancedSettingsModel,
    )


T = TypeVar("T", bound="LinuxAgentBackupJobFilesModel")


@_attrs_define
class LinuxAgentBackupJobFilesModel:
    """Backup scope settings for Veeam Agent for Linux backup jobs.

    Attributes:
        custom_files (list[str] | Unset): Array of directory paths that will be included in the backup scope.
        advanced_settings (LinuxAgentBackupJobFilesAdvancedSettingsModel | Unset): Advanced settings for files backed up
            with Veeam Agent for Linux backup job.
    """

    custom_files: list[str] | Unset = UNSET
    advanced_settings: LinuxAgentBackupJobFilesAdvancedSettingsModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        custom_files: list[str] | Unset = UNSET
        if not isinstance(self.custom_files, Unset):
            custom_files = self.custom_files

        advanced_settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.advanced_settings, Unset):
            advanced_settings = self.advanced_settings.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if custom_files is not UNSET:
            field_dict["customFiles"] = custom_files
        if advanced_settings is not UNSET:
            field_dict["advancedSettings"] = advanced_settings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.linux_agent_backup_job_files_advanced_settings_model import (
            LinuxAgentBackupJobFilesAdvancedSettingsModel,
        )

        d = dict(src_dict)
        custom_files = cast(list[str], d.pop("customFiles", UNSET))

        _advanced_settings = d.pop("advancedSettings", UNSET)
        advanced_settings: LinuxAgentBackupJobFilesAdvancedSettingsModel | Unset
        if isinstance(_advanced_settings, Unset):
            advanced_settings = UNSET
        else:
            advanced_settings = LinuxAgentBackupJobFilesAdvancedSettingsModel.from_dict(_advanced_settings)

        linux_agent_backup_job_files_model = cls(
            custom_files=custom_files,
            advanced_settings=advanced_settings,
        )

        linux_agent_backup_job_files_model.additional_properties = d
        return linux_agent_backup_job_files_model

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
