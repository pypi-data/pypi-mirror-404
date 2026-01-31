from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_postgre_sql_user_connection_type import EPostgreSQLUserConnectionType
from ..models.e_retain_log_backups_type import ERetainLogBackupsType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.backup_log_shipping_servers_import_model import BackupLogShippingServersImportModel
    from ..models.credentials_import_model import CredentialsImportModel


T = TypeVar("T", bound="BackupPostgreSQLSettingsImportModel")


@_attrs_define
class BackupPostgreSQLSettingsImportModel:
    """PostgreSQL WAL files settings.

    Attributes:
        use_guest_credentials (bool | Unset): If `true`, Veeam Backup & Replication uses credentials specified in the
            guest processing settings.
        credentials (CredentialsImportModel | Unset): Credentials used for connection.
        user_connection_type (EPostgreSQLUserConnectionType | Unset): Connection type for the PostgreSQL user.
        backup_logs (bool | Unset): If `true`, WAL files are backed up.
        backup_mins_count (int | Unset): Frequency of WAL files backup, in minutes.
        retain_log_backups (ERetainLogBackupsType | Unset): Retention policy for the logs stored in the backup
            repository.
        keep_days_count (int | Unset): Number of days to keep WAL files.
        temp_archive_logs_path (str | Unset): Temporary location where the WAL files will be stored.
        log_shipping_servers (BackupLogShippingServersImportModel | Unset): Log shipping server used to transport logs.
    """

    use_guest_credentials: bool | Unset = UNSET
    credentials: CredentialsImportModel | Unset = UNSET
    user_connection_type: EPostgreSQLUserConnectionType | Unset = UNSET
    backup_logs: bool | Unset = UNSET
    backup_mins_count: int | Unset = UNSET
    retain_log_backups: ERetainLogBackupsType | Unset = UNSET
    keep_days_count: int | Unset = UNSET
    temp_archive_logs_path: str | Unset = UNSET
    log_shipping_servers: BackupLogShippingServersImportModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        use_guest_credentials = self.use_guest_credentials

        credentials: dict[str, Any] | Unset = UNSET
        if not isinstance(self.credentials, Unset):
            credentials = self.credentials.to_dict()

        user_connection_type: str | Unset = UNSET
        if not isinstance(self.user_connection_type, Unset):
            user_connection_type = self.user_connection_type.value

        backup_logs = self.backup_logs

        backup_mins_count = self.backup_mins_count

        retain_log_backups: str | Unset = UNSET
        if not isinstance(self.retain_log_backups, Unset):
            retain_log_backups = self.retain_log_backups.value

        keep_days_count = self.keep_days_count

        temp_archive_logs_path = self.temp_archive_logs_path

        log_shipping_servers: dict[str, Any] | Unset = UNSET
        if not isinstance(self.log_shipping_servers, Unset):
            log_shipping_servers = self.log_shipping_servers.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if use_guest_credentials is not UNSET:
            field_dict["useGuestCredentials"] = use_guest_credentials
        if credentials is not UNSET:
            field_dict["credentials"] = credentials
        if user_connection_type is not UNSET:
            field_dict["userConnectionType"] = user_connection_type
        if backup_logs is not UNSET:
            field_dict["backupLogs"] = backup_logs
        if backup_mins_count is not UNSET:
            field_dict["backupMinsCount"] = backup_mins_count
        if retain_log_backups is not UNSET:
            field_dict["retainLogBackups"] = retain_log_backups
        if keep_days_count is not UNSET:
            field_dict["keepDaysCount"] = keep_days_count
        if temp_archive_logs_path is not UNSET:
            field_dict["tempArchiveLogsPath"] = temp_archive_logs_path
        if log_shipping_servers is not UNSET:
            field_dict["logShippingServers"] = log_shipping_servers

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.backup_log_shipping_servers_import_model import BackupLogShippingServersImportModel
        from ..models.credentials_import_model import CredentialsImportModel

        d = dict(src_dict)
        use_guest_credentials = d.pop("useGuestCredentials", UNSET)

        _credentials = d.pop("credentials", UNSET)
        credentials: CredentialsImportModel | Unset
        if isinstance(_credentials, Unset):
            credentials = UNSET
        else:
            credentials = CredentialsImportModel.from_dict(_credentials)

        _user_connection_type = d.pop("userConnectionType", UNSET)
        user_connection_type: EPostgreSQLUserConnectionType | Unset
        if isinstance(_user_connection_type, Unset):
            user_connection_type = UNSET
        else:
            user_connection_type = EPostgreSQLUserConnectionType(_user_connection_type)

        backup_logs = d.pop("backupLogs", UNSET)

        backup_mins_count = d.pop("backupMinsCount", UNSET)

        _retain_log_backups = d.pop("retainLogBackups", UNSET)
        retain_log_backups: ERetainLogBackupsType | Unset
        if isinstance(_retain_log_backups, Unset):
            retain_log_backups = UNSET
        else:
            retain_log_backups = ERetainLogBackupsType(_retain_log_backups)

        keep_days_count = d.pop("keepDaysCount", UNSET)

        temp_archive_logs_path = d.pop("tempArchiveLogsPath", UNSET)

        _log_shipping_servers = d.pop("logShippingServers", UNSET)
        log_shipping_servers: BackupLogShippingServersImportModel | Unset
        if isinstance(_log_shipping_servers, Unset):
            log_shipping_servers = UNSET
        else:
            log_shipping_servers = BackupLogShippingServersImportModel.from_dict(_log_shipping_servers)

        backup_postgre_sql_settings_import_model = cls(
            use_guest_credentials=use_guest_credentials,
            credentials=credentials,
            user_connection_type=user_connection_type,
            backup_logs=backup_logs,
            backup_mins_count=backup_mins_count,
            retain_log_backups=retain_log_backups,
            keep_days_count=keep_days_count,
            temp_archive_logs_path=temp_archive_logs_path,
            log_shipping_servers=log_shipping_servers,
        )

        backup_postgre_sql_settings_import_model.additional_properties = d
        return backup_postgre_sql_settings_import_model

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
