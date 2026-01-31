from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_backup_script_processing_mode import EBackupScriptProcessingMode
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.backup_linux_script_model import BackupLinuxScriptModel
    from ..models.backup_windows_script_model import BackupWindowsScriptModel


T = TypeVar("T", bound="BackupScriptSettingsModel")


@_attrs_define
class BackupScriptSettingsModel:
    """Pre-freeze and post-thaw scripts.

    Attributes:
        script_processing_mode (EBackupScriptProcessingMode): Scenario for scripts execution.
        windows_scripts (BackupWindowsScriptModel | Unset): Paths to pre-freeze and post-thaw scripts for Microsoft
            Windows VMs.
        linux_scripts (BackupLinuxScriptModel | Unset): Paths to pre-freeze and post-thaw scripts for Linux VMs.
    """

    script_processing_mode: EBackupScriptProcessingMode
    windows_scripts: BackupWindowsScriptModel | Unset = UNSET
    linux_scripts: BackupLinuxScriptModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        script_processing_mode = self.script_processing_mode.value

        windows_scripts: dict[str, Any] | Unset = UNSET
        if not isinstance(self.windows_scripts, Unset):
            windows_scripts = self.windows_scripts.to_dict()

        linux_scripts: dict[str, Any] | Unset = UNSET
        if not isinstance(self.linux_scripts, Unset):
            linux_scripts = self.linux_scripts.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "scriptProcessingMode": script_processing_mode,
            }
        )
        if windows_scripts is not UNSET:
            field_dict["windowsScripts"] = windows_scripts
        if linux_scripts is not UNSET:
            field_dict["linuxScripts"] = linux_scripts

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.backup_linux_script_model import BackupLinuxScriptModel
        from ..models.backup_windows_script_model import BackupWindowsScriptModel

        d = dict(src_dict)
        script_processing_mode = EBackupScriptProcessingMode(d.pop("scriptProcessingMode"))

        _windows_scripts = d.pop("windowsScripts", UNSET)
        windows_scripts: BackupWindowsScriptModel | Unset
        if isinstance(_windows_scripts, Unset):
            windows_scripts = UNSET
        else:
            windows_scripts = BackupWindowsScriptModel.from_dict(_windows_scripts)

        _linux_scripts = d.pop("linuxScripts", UNSET)
        linux_scripts: BackupLinuxScriptModel | Unset
        if isinstance(_linux_scripts, Unset):
            linux_scripts = UNSET
        else:
            linux_scripts = BackupLinuxScriptModel.from_dict(_linux_scripts)

        backup_script_settings_model = cls(
            script_processing_mode=script_processing_mode,
            windows_scripts=windows_scripts,
            linux_scripts=linux_scripts,
        )

        backup_script_settings_model.additional_properties = d
        return backup_script_settings_model

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
