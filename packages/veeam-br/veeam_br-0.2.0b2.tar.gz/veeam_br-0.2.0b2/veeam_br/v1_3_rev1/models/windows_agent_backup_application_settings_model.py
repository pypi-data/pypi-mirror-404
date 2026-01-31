from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_transaction_logs_settings import ETransactionLogsSettings
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.agent_backup_oracle_settings_model import AgentBackupOracleSettingsModel
    from ..models.agent_backup_sharepoint_settings_model import AgentBackupSharepointSettingsModel
    from ..models.agent_backup_sql_settings_model import AgentBackupSQLSettingsModel
    from ..models.agent_object_model import AgentObjectModel
    from ..models.windows_agent_backup_script_settings_model import WindowsAgentBackupScriptSettingsModel


T = TypeVar("T", bound="WindowsAgentBackupApplicationSettingsModel")


@_attrs_define
class WindowsAgentBackupApplicationSettingsModel:
    """Application settings.

    Attributes:
        machine_object (AgentObjectModel): Agent-managed object.
        is_processing_enabled (bool): If `true`, application-aware processing is enabled.
        transaction_logs (ETransactionLogsSettings | Unset): Transaction logs settings that define whether copy-only
            backups must be created, or transaction logs for Microsoft Exchange, Microsoft SQL and Oracle VMs must be
            processed.<p> If transaction log processing is selected, specify the following parameters:<ul> <li>[For
            Microsoft SQL Server VMs] Microsoft SQL Server transaction log settings</li> <li>[For Oracle VMs] Oracle
            archived log settings</li></ul>
        sql (AgentBackupSQLSettingsModel | Unset): Settings for Microsoft SQL Server transaction logs.
        oracle (AgentBackupOracleSettingsModel | Unset): Application-aware processing settings for Oracle databases.
        share_point (AgentBackupSharepointSettingsModel | Unset): Application-aware processing settings for Microsoft
            SharePoint databases.
        scripts (WindowsAgentBackupScriptSettingsModel | Unset): Pre-freeze and post-thaw scripts.
    """

    machine_object: AgentObjectModel
    is_processing_enabled: bool
    transaction_logs: ETransactionLogsSettings | Unset = UNSET
    sql: AgentBackupSQLSettingsModel | Unset = UNSET
    oracle: AgentBackupOracleSettingsModel | Unset = UNSET
    share_point: AgentBackupSharepointSettingsModel | Unset = UNSET
    scripts: WindowsAgentBackupScriptSettingsModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        machine_object = self.machine_object.to_dict()

        is_processing_enabled = self.is_processing_enabled

        transaction_logs: str | Unset = UNSET
        if not isinstance(self.transaction_logs, Unset):
            transaction_logs = self.transaction_logs.value

        sql: dict[str, Any] | Unset = UNSET
        if not isinstance(self.sql, Unset):
            sql = self.sql.to_dict()

        oracle: dict[str, Any] | Unset = UNSET
        if not isinstance(self.oracle, Unset):
            oracle = self.oracle.to_dict()

        share_point: dict[str, Any] | Unset = UNSET
        if not isinstance(self.share_point, Unset):
            share_point = self.share_point.to_dict()

        scripts: dict[str, Any] | Unset = UNSET
        if not isinstance(self.scripts, Unset):
            scripts = self.scripts.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "machineObject": machine_object,
                "isProcessingEnabled": is_processing_enabled,
            }
        )
        if transaction_logs is not UNSET:
            field_dict["transactionLogs"] = transaction_logs
        if sql is not UNSET:
            field_dict["sql"] = sql
        if oracle is not UNSET:
            field_dict["oracle"] = oracle
        if share_point is not UNSET:
            field_dict["sharePoint"] = share_point
        if scripts is not UNSET:
            field_dict["scripts"] = scripts

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.agent_backup_oracle_settings_model import AgentBackupOracleSettingsModel
        from ..models.agent_backup_sharepoint_settings_model import AgentBackupSharepointSettingsModel
        from ..models.agent_backup_sql_settings_model import AgentBackupSQLSettingsModel
        from ..models.agent_object_model import AgentObjectModel
        from ..models.windows_agent_backup_script_settings_model import WindowsAgentBackupScriptSettingsModel

        d = dict(src_dict)
        machine_object = AgentObjectModel.from_dict(d.pop("machineObject"))

        is_processing_enabled = d.pop("isProcessingEnabled")

        _transaction_logs = d.pop("transactionLogs", UNSET)
        transaction_logs: ETransactionLogsSettings | Unset
        if isinstance(_transaction_logs, Unset):
            transaction_logs = UNSET
        else:
            transaction_logs = ETransactionLogsSettings(_transaction_logs)

        _sql = d.pop("sql", UNSET)
        sql: AgentBackupSQLSettingsModel | Unset
        if isinstance(_sql, Unset):
            sql = UNSET
        else:
            sql = AgentBackupSQLSettingsModel.from_dict(_sql)

        _oracle = d.pop("oracle", UNSET)
        oracle: AgentBackupOracleSettingsModel | Unset
        if isinstance(_oracle, Unset):
            oracle = UNSET
        else:
            oracle = AgentBackupOracleSettingsModel.from_dict(_oracle)

        _share_point = d.pop("sharePoint", UNSET)
        share_point: AgentBackupSharepointSettingsModel | Unset
        if isinstance(_share_point, Unset):
            share_point = UNSET
        else:
            share_point = AgentBackupSharepointSettingsModel.from_dict(_share_point)

        _scripts = d.pop("scripts", UNSET)
        scripts: WindowsAgentBackupScriptSettingsModel | Unset
        if isinstance(_scripts, Unset):
            scripts = UNSET
        else:
            scripts = WindowsAgentBackupScriptSettingsModel.from_dict(_scripts)

        windows_agent_backup_application_settings_model = cls(
            machine_object=machine_object,
            is_processing_enabled=is_processing_enabled,
            transaction_logs=transaction_logs,
            sql=sql,
            oracle=oracle,
            share_point=share_point,
            scripts=scripts,
        )

        windows_agent_backup_application_settings_model.additional_properties = d
        return windows_agent_backup_application_settings_model

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
