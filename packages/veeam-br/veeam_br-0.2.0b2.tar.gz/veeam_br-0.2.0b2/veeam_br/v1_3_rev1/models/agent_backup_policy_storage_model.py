from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.agent_backup_policy_advanced_settings_model import AgentBackupPolicyAdvancedSettingsModel
    from ..models.agent_backup_policy_destination_model import AgentBackupPolicyDestinationModel
    from ..models.backup_job_retention_policy_settings_model import BackupJobRetentionPolicySettingsModel
    from ..models.gfs_policy_settings_model import GFSPolicySettingsModel


T = TypeVar("T", bound="AgentBackupPolicyStorageModel")


@_attrs_define
class AgentBackupPolicyStorageModel:
    """Backup policy storage settings

    Attributes:
        destination (AgentBackupPolicyDestinationModel): Settings for destination of Veeam Agent backup policy.
        retention_policy (BackupJobRetentionPolicySettingsModel | Unset): Retention policy settings.
        gfs_policy (GFSPolicySettingsModel | Unset): GFS retention policy settings.
        advanced_settings (AgentBackupPolicyAdvancedSettingsModel | Unset): Advanced settings for Veeam Agent backup
            policies.
    """

    destination: AgentBackupPolicyDestinationModel
    retention_policy: BackupJobRetentionPolicySettingsModel | Unset = UNSET
    gfs_policy: GFSPolicySettingsModel | Unset = UNSET
    advanced_settings: AgentBackupPolicyAdvancedSettingsModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        destination = self.destination.to_dict()

        retention_policy: dict[str, Any] | Unset = UNSET
        if not isinstance(self.retention_policy, Unset):
            retention_policy = self.retention_policy.to_dict()

        gfs_policy: dict[str, Any] | Unset = UNSET
        if not isinstance(self.gfs_policy, Unset):
            gfs_policy = self.gfs_policy.to_dict()

        advanced_settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.advanced_settings, Unset):
            advanced_settings = self.advanced_settings.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "destination": destination,
            }
        )
        if retention_policy is not UNSET:
            field_dict["retentionPolicy"] = retention_policy
        if gfs_policy is not UNSET:
            field_dict["gfsPolicy"] = gfs_policy
        if advanced_settings is not UNSET:
            field_dict["advancedSettings"] = advanced_settings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.agent_backup_policy_advanced_settings_model import AgentBackupPolicyAdvancedSettingsModel
        from ..models.agent_backup_policy_destination_model import AgentBackupPolicyDestinationModel
        from ..models.backup_job_retention_policy_settings_model import BackupJobRetentionPolicySettingsModel
        from ..models.gfs_policy_settings_model import GFSPolicySettingsModel

        d = dict(src_dict)
        destination = AgentBackupPolicyDestinationModel.from_dict(d.pop("destination"))

        _retention_policy = d.pop("retentionPolicy", UNSET)
        retention_policy: BackupJobRetentionPolicySettingsModel | Unset
        if isinstance(_retention_policy, Unset):
            retention_policy = UNSET
        else:
            retention_policy = BackupJobRetentionPolicySettingsModel.from_dict(_retention_policy)

        _gfs_policy = d.pop("gfsPolicy", UNSET)
        gfs_policy: GFSPolicySettingsModel | Unset
        if isinstance(_gfs_policy, Unset):
            gfs_policy = UNSET
        else:
            gfs_policy = GFSPolicySettingsModel.from_dict(_gfs_policy)

        _advanced_settings = d.pop("advancedSettings", UNSET)
        advanced_settings: AgentBackupPolicyAdvancedSettingsModel | Unset
        if isinstance(_advanced_settings, Unset):
            advanced_settings = UNSET
        else:
            advanced_settings = AgentBackupPolicyAdvancedSettingsModel.from_dict(_advanced_settings)

        agent_backup_policy_storage_model = cls(
            destination=destination,
            retention_policy=retention_policy,
            gfs_policy=gfs_policy,
            advanced_settings=advanced_settings,
        )

        agent_backup_policy_storage_model.additional_properties = d
        return agent_backup_policy_storage_model

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
