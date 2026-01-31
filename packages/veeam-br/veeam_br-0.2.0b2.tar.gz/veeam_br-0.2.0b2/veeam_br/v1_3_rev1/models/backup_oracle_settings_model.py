from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_backup_oracle_logs_settings import EBackupOracleLogsSettings
from ..models.e_retain_log_backups_type import ERetainLogBackupsType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.backup_log_shipping_servers_model import BackupLogShippingServersModel


T = TypeVar("T", bound="BackupOracleSettingsModel")


@_attrs_define
class BackupOracleSettingsModel:
    """Oracle archived log settings.

    Attributes:
        use_guest_credentials (bool): If `true`, Veeam Backup & Replication uses credentials specified in the guest
            processing settings.
        archive_logs (EBackupOracleLogsSettings): Type of archived logs processing.
        credentials_id (UUID | Unset): ID of the credentials record that is used if `useGuestCredentials` is *false*.
        delete_hours_count (int | Unset): Time period in hours to keep archived logs. This parameter should be specified
            if the `EBackupOracleLogsSettings` value is *deleteExpiredHours*.
        delete_g_bs_count (int | Unset): Maximum size for archived logs in GB. This parameter should be specified if the
            `EBackupOracleLogsSettings` value is *deleteExpiredGBs*.
        backup_logs (bool | Unset): If `true`, archived logs are backed up.
        backup_mins_count (int | Unset): Frequency of archived log backup, in minutes.
        retain_log_backups (ERetainLogBackupsType | Unset): Retention policy for the logs stored in the backup
            repository.
        keep_days_count (int | Unset): Number of days to keep archived logs.
        log_shipping_servers (BackupLogShippingServersModel | Unset): Log shipping server used to transport logs.
    """

    use_guest_credentials: bool
    archive_logs: EBackupOracleLogsSettings
    credentials_id: UUID | Unset = UNSET
    delete_hours_count: int | Unset = UNSET
    delete_g_bs_count: int | Unset = UNSET
    backup_logs: bool | Unset = UNSET
    backup_mins_count: int | Unset = UNSET
    retain_log_backups: ERetainLogBackupsType | Unset = UNSET
    keep_days_count: int | Unset = UNSET
    log_shipping_servers: BackupLogShippingServersModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        use_guest_credentials = self.use_guest_credentials

        archive_logs = self.archive_logs.value

        credentials_id: str | Unset = UNSET
        if not isinstance(self.credentials_id, Unset):
            credentials_id = str(self.credentials_id)

        delete_hours_count = self.delete_hours_count

        delete_g_bs_count = self.delete_g_bs_count

        backup_logs = self.backup_logs

        backup_mins_count = self.backup_mins_count

        retain_log_backups: str | Unset = UNSET
        if not isinstance(self.retain_log_backups, Unset):
            retain_log_backups = self.retain_log_backups.value

        keep_days_count = self.keep_days_count

        log_shipping_servers: dict[str, Any] | Unset = UNSET
        if not isinstance(self.log_shipping_servers, Unset):
            log_shipping_servers = self.log_shipping_servers.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "useGuestCredentials": use_guest_credentials,
                "archiveLogs": archive_logs,
            }
        )
        if credentials_id is not UNSET:
            field_dict["credentialsId"] = credentials_id
        if delete_hours_count is not UNSET:
            field_dict["deleteHoursCount"] = delete_hours_count
        if delete_g_bs_count is not UNSET:
            field_dict["deleteGBsCount"] = delete_g_bs_count
        if backup_logs is not UNSET:
            field_dict["backupLogs"] = backup_logs
        if backup_mins_count is not UNSET:
            field_dict["backupMinsCount"] = backup_mins_count
        if retain_log_backups is not UNSET:
            field_dict["retainLogBackups"] = retain_log_backups
        if keep_days_count is not UNSET:
            field_dict["keepDaysCount"] = keep_days_count
        if log_shipping_servers is not UNSET:
            field_dict["logShippingServers"] = log_shipping_servers

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.backup_log_shipping_servers_model import BackupLogShippingServersModel

        d = dict(src_dict)
        use_guest_credentials = d.pop("useGuestCredentials")

        archive_logs = EBackupOracleLogsSettings(d.pop("archiveLogs"))

        _credentials_id = d.pop("credentialsId", UNSET)
        credentials_id: UUID | Unset
        if isinstance(_credentials_id, Unset):
            credentials_id = UNSET
        else:
            credentials_id = UUID(_credentials_id)

        delete_hours_count = d.pop("deleteHoursCount", UNSET)

        delete_g_bs_count = d.pop("deleteGBsCount", UNSET)

        backup_logs = d.pop("backupLogs", UNSET)

        backup_mins_count = d.pop("backupMinsCount", UNSET)

        _retain_log_backups = d.pop("retainLogBackups", UNSET)
        retain_log_backups: ERetainLogBackupsType | Unset
        if isinstance(_retain_log_backups, Unset):
            retain_log_backups = UNSET
        else:
            retain_log_backups = ERetainLogBackupsType(_retain_log_backups)

        keep_days_count = d.pop("keepDaysCount", UNSET)

        _log_shipping_servers = d.pop("logShippingServers", UNSET)
        log_shipping_servers: BackupLogShippingServersModel | Unset
        if isinstance(_log_shipping_servers, Unset):
            log_shipping_servers = UNSET
        else:
            log_shipping_servers = BackupLogShippingServersModel.from_dict(_log_shipping_servers)

        backup_oracle_settings_model = cls(
            use_guest_credentials=use_guest_credentials,
            archive_logs=archive_logs,
            credentials_id=credentials_id,
            delete_hours_count=delete_hours_count,
            delete_g_bs_count=delete_g_bs_count,
            backup_logs=backup_logs,
            backup_mins_count=backup_mins_count,
            retain_log_backups=retain_log_backups,
            keep_days_count=keep_days_count,
            log_shipping_servers=log_shipping_servers,
        )

        backup_oracle_settings_model.additional_properties = d
        return backup_oracle_settings_model

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
