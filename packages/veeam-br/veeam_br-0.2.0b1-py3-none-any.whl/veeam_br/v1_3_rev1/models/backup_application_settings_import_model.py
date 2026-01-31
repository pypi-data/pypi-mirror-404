from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_application_settings_vss import EApplicationSettingsVSS
from ..models.e_transaction_logs_settings import ETransactionLogsSettings
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.backup_fs_exclusions_model import BackupFSExclusionsModel
    from ..models.backup_oracle_settings_import_model import BackupOracleSettingsImportModel
    from ..models.backup_postgre_sql_settings_import_model import BackupPostgreSQLSettingsImportModel
    from ..models.backup_script_settings_model import BackupScriptSettingsModel
    from ..models.backup_sql_settings_import_model import BackupSQLSettingsImportModel
    from ..models.inventory_object_model import InventoryObjectModel


T = TypeVar("T", bound="BackupApplicationSettingsImportModel")


@_attrs_define
class BackupApplicationSettingsImportModel:
    """Application settings.

    Attributes:
        vm_object (InventoryObjectModel): Inventory object properties.
        vss (EApplicationSettingsVSS): Behavior scenario for application-aware processing.
        use_persistent_guest_agent (bool | Unset): If `true`, persistent guest agent is used.
        transaction_logs (ETransactionLogsSettings | Unset): Transaction logs settings that define whether copy-only
            backups must be created, or transaction logs for Microsoft Exchange, Microsoft SQL and Oracle VMs must be
            processed.<p> If transaction log processing is selected, specify the following parameters:<ul> <li>[For
            Microsoft SQL Server VMs] Microsoft SQL Server transaction log settings</li> <li>[For Oracle VMs] Oracle
            archived log settings</li></ul>
        sql (BackupSQLSettingsImportModel | Unset): Microsoft SQL Server transaction log settings.
        oracle (BackupOracleSettingsImportModel | Unset): Oracle archived log settings.
        postgre_sql (BackupPostgreSQLSettingsImportModel | Unset): PostgreSQL WAL files settings.
        exclusions (BackupFSExclusionsModel | Unset): VM guest OS file exclusion.
        scripts (BackupScriptSettingsModel | Unset): Pre-freeze and post-thaw scripts.
    """

    vm_object: InventoryObjectModel
    vss: EApplicationSettingsVSS
    use_persistent_guest_agent: bool | Unset = UNSET
    transaction_logs: ETransactionLogsSettings | Unset = UNSET
    sql: BackupSQLSettingsImportModel | Unset = UNSET
    oracle: BackupOracleSettingsImportModel | Unset = UNSET
    postgre_sql: BackupPostgreSQLSettingsImportModel | Unset = UNSET
    exclusions: BackupFSExclusionsModel | Unset = UNSET
    scripts: BackupScriptSettingsModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        vm_object = self.vm_object.to_dict()

        vss = self.vss.value

        use_persistent_guest_agent = self.use_persistent_guest_agent

        transaction_logs: str | Unset = UNSET
        if not isinstance(self.transaction_logs, Unset):
            transaction_logs = self.transaction_logs.value

        sql: dict[str, Any] | Unset = UNSET
        if not isinstance(self.sql, Unset):
            sql = self.sql.to_dict()

        oracle: dict[str, Any] | Unset = UNSET
        if not isinstance(self.oracle, Unset):
            oracle = self.oracle.to_dict()

        postgre_sql: dict[str, Any] | Unset = UNSET
        if not isinstance(self.postgre_sql, Unset):
            postgre_sql = self.postgre_sql.to_dict()

        exclusions: dict[str, Any] | Unset = UNSET
        if not isinstance(self.exclusions, Unset):
            exclusions = self.exclusions.to_dict()

        scripts: dict[str, Any] | Unset = UNSET
        if not isinstance(self.scripts, Unset):
            scripts = self.scripts.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "vmObject": vm_object,
                "vss": vss,
            }
        )
        if use_persistent_guest_agent is not UNSET:
            field_dict["usePersistentGuestAgent"] = use_persistent_guest_agent
        if transaction_logs is not UNSET:
            field_dict["transactionLogs"] = transaction_logs
        if sql is not UNSET:
            field_dict["sql"] = sql
        if oracle is not UNSET:
            field_dict["oracle"] = oracle
        if postgre_sql is not UNSET:
            field_dict["postgreSQL"] = postgre_sql
        if exclusions is not UNSET:
            field_dict["exclusions"] = exclusions
        if scripts is not UNSET:
            field_dict["scripts"] = scripts

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.backup_fs_exclusions_model import BackupFSExclusionsModel
        from ..models.backup_oracle_settings_import_model import BackupOracleSettingsImportModel
        from ..models.backup_postgre_sql_settings_import_model import BackupPostgreSQLSettingsImportModel
        from ..models.backup_script_settings_model import BackupScriptSettingsModel
        from ..models.backup_sql_settings_import_model import BackupSQLSettingsImportModel
        from ..models.inventory_object_model import InventoryObjectModel

        d = dict(src_dict)
        vm_object = InventoryObjectModel.from_dict(d.pop("vmObject"))

        vss = EApplicationSettingsVSS(d.pop("vss"))

        use_persistent_guest_agent = d.pop("usePersistentGuestAgent", UNSET)

        _transaction_logs = d.pop("transactionLogs", UNSET)
        transaction_logs: ETransactionLogsSettings | Unset
        if isinstance(_transaction_logs, Unset):
            transaction_logs = UNSET
        else:
            transaction_logs = ETransactionLogsSettings(_transaction_logs)

        _sql = d.pop("sql", UNSET)
        sql: BackupSQLSettingsImportModel | Unset
        if isinstance(_sql, Unset):
            sql = UNSET
        else:
            sql = BackupSQLSettingsImportModel.from_dict(_sql)

        _oracle = d.pop("oracle", UNSET)
        oracle: BackupOracleSettingsImportModel | Unset
        if isinstance(_oracle, Unset):
            oracle = UNSET
        else:
            oracle = BackupOracleSettingsImportModel.from_dict(_oracle)

        _postgre_sql = d.pop("postgreSQL", UNSET)
        postgre_sql: BackupPostgreSQLSettingsImportModel | Unset
        if isinstance(_postgre_sql, Unset):
            postgre_sql = UNSET
        else:
            postgre_sql = BackupPostgreSQLSettingsImportModel.from_dict(_postgre_sql)

        _exclusions = d.pop("exclusions", UNSET)
        exclusions: BackupFSExclusionsModel | Unset
        if isinstance(_exclusions, Unset):
            exclusions = UNSET
        else:
            exclusions = BackupFSExclusionsModel.from_dict(_exclusions)

        _scripts = d.pop("scripts", UNSET)
        scripts: BackupScriptSettingsModel | Unset
        if isinstance(_scripts, Unset):
            scripts = UNSET
        else:
            scripts = BackupScriptSettingsModel.from_dict(_scripts)

        backup_application_settings_import_model = cls(
            vm_object=vm_object,
            vss=vss,
            use_persistent_guest_agent=use_persistent_guest_agent,
            transaction_logs=transaction_logs,
            sql=sql,
            oracle=oracle,
            postgre_sql=postgre_sql,
            exclusions=exclusions,
            scripts=scripts,
        )

        backup_application_settings_import_model.additional_properties = d
        return backup_application_settings_import_model

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
