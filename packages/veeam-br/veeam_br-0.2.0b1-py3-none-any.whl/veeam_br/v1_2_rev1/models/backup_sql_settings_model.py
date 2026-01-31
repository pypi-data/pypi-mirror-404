from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_retain_log_backups_type import ERetainLogBackupsType
from ..models.esql_logs_processing import ESQLLogsProcessing
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.backup_log_shipping_servers_model import BackupLogShippingServersModel


T = TypeVar("T", bound="BackupSQLSettingsModel")


@_attrs_define
class BackupSQLSettingsModel:
    """Microsoft SQL Server transaction log settings.

    Attributes:
        logs_processing (ESQLLogsProcessing): Type of transaction logs processing.
        backup_mins_count (int | Unset): Frequency of transaction log backup, in minutes.
        retain_log_backups (ERetainLogBackupsType | Unset): Retention policy for the logs stored in the backup
            repository.
        keep_days_count (int | Unset): Number of days to keep transaction logs in the backup repository.
        log_shipping_servers (BackupLogShippingServersModel | Unset): Log shipping server used to transport logs.
    """

    logs_processing: ESQLLogsProcessing
    backup_mins_count: int | Unset = UNSET
    retain_log_backups: ERetainLogBackupsType | Unset = UNSET
    keep_days_count: int | Unset = UNSET
    log_shipping_servers: BackupLogShippingServersModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        logs_processing = self.logs_processing.value

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
                "logsProcessing": logs_processing,
            }
        )
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
        logs_processing = ESQLLogsProcessing(d.pop("logsProcessing"))

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

        backup_sql_settings_model = cls(
            logs_processing=logs_processing,
            backup_mins_count=backup_mins_count,
            retain_log_backups=retain_log_backups,
            keep_days_count=keep_days_count,
            log_shipping_servers=log_shipping_servers,
        )

        backup_sql_settings_model.additional_properties = d
        return backup_sql_settings_model

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
