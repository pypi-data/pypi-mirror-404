from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_backup_script_processing_mode import EBackupScriptProcessingMode
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.backup_windows_script_model import BackupWindowsScriptModel


T = TypeVar("T", bound="WindowsAgentBackupScriptSettingsModel")


@_attrs_define
class WindowsAgentBackupScriptSettingsModel:
    """Pre-freeze and post-thaw scripts.

    Attributes:
        script_processing_mode (EBackupScriptProcessingMode): Scenario for scripts execution.
        snapshot_scripts (BackupWindowsScriptModel | Unset): Paths to pre-freeze and post-thaw scripts for Microsoft
            Windows VMs.
    """

    script_processing_mode: EBackupScriptProcessingMode
    snapshot_scripts: BackupWindowsScriptModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        script_processing_mode = self.script_processing_mode.value

        snapshot_scripts: dict[str, Any] | Unset = UNSET
        if not isinstance(self.snapshot_scripts, Unset):
            snapshot_scripts = self.snapshot_scripts.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "scriptProcessingMode": script_processing_mode,
            }
        )
        if snapshot_scripts is not UNSET:
            field_dict["snapshotScripts"] = snapshot_scripts

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.backup_windows_script_model import BackupWindowsScriptModel

        d = dict(src_dict)
        script_processing_mode = EBackupScriptProcessingMode(d.pop("scriptProcessingMode"))

        _snapshot_scripts = d.pop("snapshotScripts", UNSET)
        snapshot_scripts: BackupWindowsScriptModel | Unset
        if isinstance(_snapshot_scripts, Unset):
            snapshot_scripts = UNSET
        else:
            snapshot_scripts = BackupWindowsScriptModel.from_dict(_snapshot_scripts)

        windows_agent_backup_script_settings_model = cls(
            script_processing_mode=script_processing_mode,
            snapshot_scripts=snapshot_scripts,
        )

        windows_agent_backup_script_settings_model.additional_properties = d
        return windows_agent_backup_script_settings_model

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
