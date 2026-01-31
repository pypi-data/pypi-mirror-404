from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.backup_job_script_model import BackupJobScriptModel
    from ..models.backup_linux_script_model import BackupLinuxScriptModel


T = TypeVar("T", bound="LinuxAgentBackupScriptSettingsModel")


@_attrs_define
class LinuxAgentBackupScriptSettingsModel:
    """Pre-freeze and post-thaw scripts.

    Attributes:
        is_execution_enabled (bool | Unset): If `true`, execution of the scripts is enabled.
        job_scripts (BackupJobScriptModel | Unset): Paths to pre-freeze and post-thaw scripts.
        snapshot_scripts (BackupLinuxScriptModel | Unset): Paths to pre-freeze and post-thaw scripts for Linux VMs.
    """

    is_execution_enabled: bool | Unset = UNSET
    job_scripts: BackupJobScriptModel | Unset = UNSET
    snapshot_scripts: BackupLinuxScriptModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        is_execution_enabled = self.is_execution_enabled

        job_scripts: dict[str, Any] | Unset = UNSET
        if not isinstance(self.job_scripts, Unset):
            job_scripts = self.job_scripts.to_dict()

        snapshot_scripts: dict[str, Any] | Unset = UNSET
        if not isinstance(self.snapshot_scripts, Unset):
            snapshot_scripts = self.snapshot_scripts.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if is_execution_enabled is not UNSET:
            field_dict["isExecutionEnabled"] = is_execution_enabled
        if job_scripts is not UNSET:
            field_dict["jobScripts"] = job_scripts
        if snapshot_scripts is not UNSET:
            field_dict["snapshotScripts"] = snapshot_scripts

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.backup_job_script_model import BackupJobScriptModel
        from ..models.backup_linux_script_model import BackupLinuxScriptModel

        d = dict(src_dict)
        is_execution_enabled = d.pop("isExecutionEnabled", UNSET)

        _job_scripts = d.pop("jobScripts", UNSET)
        job_scripts: BackupJobScriptModel | Unset
        if isinstance(_job_scripts, Unset):
            job_scripts = UNSET
        else:
            job_scripts = BackupJobScriptModel.from_dict(_job_scripts)

        _snapshot_scripts = d.pop("snapshotScripts", UNSET)
        snapshot_scripts: BackupLinuxScriptModel | Unset
        if isinstance(_snapshot_scripts, Unset):
            snapshot_scripts = UNSET
        else:
            snapshot_scripts = BackupLinuxScriptModel.from_dict(_snapshot_scripts)

        linux_agent_backup_script_settings_model = cls(
            is_execution_enabled=is_execution_enabled,
            job_scripts=job_scripts,
            snapshot_scripts=snapshot_scripts,
        )

        linux_agent_backup_script_settings_model.additional_properties = d
        return linux_agent_backup_script_settings_model

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
