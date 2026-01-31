from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.agent_backup_job_personal_files_inclusion_model import AgentBackupJobPersonalFilesInclusionModel
    from ..models.agent_backup_personal_files_exclusion_model import AgentBackupPersonalFilesExclusionModel


T = TypeVar("T", bound="AgentBackupJobPersonalFilesSettingsModel")


@_attrs_define
class AgentBackupJobPersonalFilesSettingsModel:
    """Scope of personal data backed up with Veeam Agent backup job.

    Attributes:
        backup_personal_files (bool | Unset): If `true`, the backup job will back up personal files.
        includes (AgentBackupJobPersonalFilesInclusionModel | Unset): Scope of personal data included in Agent backup
            job.
        excludes (AgentBackupPersonalFilesExclusionModel | Unset): Scope of personal data excluded from Agent backup
            job.
    """

    backup_personal_files: bool | Unset = UNSET
    includes: AgentBackupJobPersonalFilesInclusionModel | Unset = UNSET
    excludes: AgentBackupPersonalFilesExclusionModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        backup_personal_files = self.backup_personal_files

        includes: dict[str, Any] | Unset = UNSET
        if not isinstance(self.includes, Unset):
            includes = self.includes.to_dict()

        excludes: dict[str, Any] | Unset = UNSET
        if not isinstance(self.excludes, Unset):
            excludes = self.excludes.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if backup_personal_files is not UNSET:
            field_dict["backupPersonalFiles"] = backup_personal_files
        if includes is not UNSET:
            field_dict["includes"] = includes
        if excludes is not UNSET:
            field_dict["excludes"] = excludes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.agent_backup_job_personal_files_inclusion_model import AgentBackupJobPersonalFilesInclusionModel
        from ..models.agent_backup_personal_files_exclusion_model import AgentBackupPersonalFilesExclusionModel

        d = dict(src_dict)
        backup_personal_files = d.pop("backupPersonalFiles", UNSET)

        _includes = d.pop("includes", UNSET)
        includes: AgentBackupJobPersonalFilesInclusionModel | Unset
        if isinstance(_includes, Unset):
            includes = UNSET
        else:
            includes = AgentBackupJobPersonalFilesInclusionModel.from_dict(_includes)

        _excludes = d.pop("excludes", UNSET)
        excludes: AgentBackupPersonalFilesExclusionModel | Unset
        if isinstance(_excludes, Unset):
            excludes = UNSET
        else:
            excludes = AgentBackupPersonalFilesExclusionModel.from_dict(_excludes)

        agent_backup_job_personal_files_settings_model = cls(
            backup_personal_files=backup_personal_files,
            includes=includes,
            excludes=excludes,
        )

        agent_backup_job_personal_files_settings_model.additional_properties = d
        return agent_backup_job_personal_files_settings_model

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
