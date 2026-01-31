from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_retain_log_backups_type import ERetainLogBackupsType
from ..models.esql_logs_processing import ESQLLogsProcessing
from ..types import UNSET, Unset

T = TypeVar("T", bound="AgentBackupSQLSettingsModel")


@_attrs_define
class AgentBackupSQLSettingsModel:
    """Settings for Microsoft SQL Server transaction logs.

    Attributes:
        logs_processing (ESQLLogsProcessing): Type of transaction logs processing.
        use_guest_credentials (bool | Unset): If `true`, Veeam Backup & Replication uses credentials specified in the
            guest processing settings.
        credentials_id (UUID | Unset): Credentials ID.
        backup_mins_count (int | Unset): Frequency of transaction log backup, in minutes.
        retain_log_backups (ERetainLogBackupsType | Unset): Retention policy for the logs stored in the backup
            repository.
        keep_days_count (int | Unset): Number of days to keep transaction logs in the backup repository.
    """

    logs_processing: ESQLLogsProcessing
    use_guest_credentials: bool | Unset = UNSET
    credentials_id: UUID | Unset = UNSET
    backup_mins_count: int | Unset = UNSET
    retain_log_backups: ERetainLogBackupsType | Unset = UNSET
    keep_days_count: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        logs_processing = self.logs_processing.value

        use_guest_credentials = self.use_guest_credentials

        credentials_id: str | Unset = UNSET
        if not isinstance(self.credentials_id, Unset):
            credentials_id = str(self.credentials_id)

        backup_mins_count = self.backup_mins_count

        retain_log_backups: str | Unset = UNSET
        if not isinstance(self.retain_log_backups, Unset):
            retain_log_backups = self.retain_log_backups.value

        keep_days_count = self.keep_days_count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "logsProcessing": logs_processing,
            }
        )
        if use_guest_credentials is not UNSET:
            field_dict["useGuestCredentials"] = use_guest_credentials
        if credentials_id is not UNSET:
            field_dict["credentialsId"] = credentials_id
        if backup_mins_count is not UNSET:
            field_dict["backupMinsCount"] = backup_mins_count
        if retain_log_backups is not UNSET:
            field_dict["retainLogBackups"] = retain_log_backups
        if keep_days_count is not UNSET:
            field_dict["keepDaysCount"] = keep_days_count

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        logs_processing = ESQLLogsProcessing(d.pop("logsProcessing"))

        use_guest_credentials = d.pop("useGuestCredentials", UNSET)

        _credentials_id = d.pop("credentialsId", UNSET)
        credentials_id: UUID | Unset
        if isinstance(_credentials_id, Unset):
            credentials_id = UNSET
        else:
            credentials_id = UUID(_credentials_id)

        backup_mins_count = d.pop("backupMinsCount", UNSET)

        _retain_log_backups = d.pop("retainLogBackups", UNSET)
        retain_log_backups: ERetainLogBackupsType | Unset
        if isinstance(_retain_log_backups, Unset):
            retain_log_backups = UNSET
        else:
            retain_log_backups = ERetainLogBackupsType(_retain_log_backups)

        keep_days_count = d.pop("keepDaysCount", UNSET)

        agent_backup_sql_settings_model = cls(
            logs_processing=logs_processing,
            use_guest_credentials=use_guest_credentials,
            credentials_id=credentials_id,
            backup_mins_count=backup_mins_count,
            retain_log_backups=retain_log_backups,
            keep_days_count=keep_days_count,
        )

        agent_backup_sql_settings_model.additional_properties = d
        return agent_backup_sql_settings_model

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
