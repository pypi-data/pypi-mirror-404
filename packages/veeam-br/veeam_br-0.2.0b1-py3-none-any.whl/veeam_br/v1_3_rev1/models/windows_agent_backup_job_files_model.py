from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.agent_backup_job_personal_files_settings_model import AgentBackupJobPersonalFilesSettingsModel
    from ..models.windows_agent_backup_job_personal_files_advanced_settings_model import (
        WindowsAgentBackupJobPersonalFilesAdvancedSettingsModel,
    )


T = TypeVar("T", bound="WindowsAgentBackupJobFilesModel")


@_attrs_define
class WindowsAgentBackupJobFilesModel:
    """Backup scope settings for Veeam Agent for Microsoft Windows backup job.

    Attributes:
        backup_os (bool | Unset): If `true`, OS-related data will be included in the backup scope.
        personal_files (AgentBackupJobPersonalFilesSettingsModel | Unset): Scope of personal data backed up with Veeam
            Agent backup job.
        custom_files (list[str] | Unset): Array of folder paths that will be included in the backup scope.
        advanced_settings (WindowsAgentBackupJobPersonalFilesAdvancedSettingsModel | Unset): Advanced settings for
            personal data backed up with Veeam Agent for Microsoft Windows backup job.
    """

    backup_os: bool | Unset = UNSET
    personal_files: AgentBackupJobPersonalFilesSettingsModel | Unset = UNSET
    custom_files: list[str] | Unset = UNSET
    advanced_settings: WindowsAgentBackupJobPersonalFilesAdvancedSettingsModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        backup_os = self.backup_os

        personal_files: dict[str, Any] | Unset = UNSET
        if not isinstance(self.personal_files, Unset):
            personal_files = self.personal_files.to_dict()

        custom_files: list[str] | Unset = UNSET
        if not isinstance(self.custom_files, Unset):
            custom_files = self.custom_files

        advanced_settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.advanced_settings, Unset):
            advanced_settings = self.advanced_settings.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if backup_os is not UNSET:
            field_dict["backupOS"] = backup_os
        if personal_files is not UNSET:
            field_dict["personalFiles"] = personal_files
        if custom_files is not UNSET:
            field_dict["customFiles"] = custom_files
        if advanced_settings is not UNSET:
            field_dict["advancedSettings"] = advanced_settings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.agent_backup_job_personal_files_settings_model import AgentBackupJobPersonalFilesSettingsModel
        from ..models.windows_agent_backup_job_personal_files_advanced_settings_model import (
            WindowsAgentBackupJobPersonalFilesAdvancedSettingsModel,
        )

        d = dict(src_dict)
        backup_os = d.pop("backupOS", UNSET)

        _personal_files = d.pop("personalFiles", UNSET)
        personal_files: AgentBackupJobPersonalFilesSettingsModel | Unset
        if isinstance(_personal_files, Unset):
            personal_files = UNSET
        else:
            personal_files = AgentBackupJobPersonalFilesSettingsModel.from_dict(_personal_files)

        custom_files = cast(list[str], d.pop("customFiles", UNSET))

        _advanced_settings = d.pop("advancedSettings", UNSET)
        advanced_settings: WindowsAgentBackupJobPersonalFilesAdvancedSettingsModel | Unset
        if isinstance(_advanced_settings, Unset):
            advanced_settings = UNSET
        else:
            advanced_settings = WindowsAgentBackupJobPersonalFilesAdvancedSettingsModel.from_dict(_advanced_settings)

        windows_agent_backup_job_files_model = cls(
            backup_os=backup_os,
            personal_files=personal_files,
            custom_files=custom_files,
            advanced_settings=advanced_settings,
        )

        windows_agent_backup_job_files_model.additional_properties = d
        return windows_agent_backup_job_files_model

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
