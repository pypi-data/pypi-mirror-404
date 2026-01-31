from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_application_settings_vss import EApplicationSettingsVSS
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.agent_backup_my_sql_settings_model import AgentBackupMySQLSettingsModel
    from ..models.agent_backup_oracle_settings_model import AgentBackupOracleSettingsModel
    from ..models.agent_object_model import AgentObjectModel
    from ..models.linux_agent_backup_script_settings_model import LinuxAgentBackupScriptSettingsModel
    from ..models.postgre_sql_settings_model import PostgreSQLSettingsModel


T = TypeVar("T", bound="LinuxAgentBackupApplicationSettingsModel")


@_attrs_define
class LinuxAgentBackupApplicationSettingsModel:
    """Application settings for a protected Linux machine.

    Attributes:
        machine_object (AgentObjectModel): Agent-managed object.
        vss (EApplicationSettingsVSS): Behavior scenario for application-aware processing.
        oracle (AgentBackupOracleSettingsModel | Unset): Application-aware processing settings for Oracle databases.
        my_sql (AgentBackupMySQLSettingsModel | Unset): Application-aware processing settings for MySQL databases.
        postgre_sql (PostgreSQLSettingsModel | Unset): Application-aware processing settings for PostgreSQL databases.
        scripts (LinuxAgentBackupScriptSettingsModel | Unset): Pre-freeze and post-thaw scripts.
    """

    machine_object: AgentObjectModel
    vss: EApplicationSettingsVSS
    oracle: AgentBackupOracleSettingsModel | Unset = UNSET
    my_sql: AgentBackupMySQLSettingsModel | Unset = UNSET
    postgre_sql: PostgreSQLSettingsModel | Unset = UNSET
    scripts: LinuxAgentBackupScriptSettingsModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        machine_object = self.machine_object.to_dict()

        vss = self.vss.value

        oracle: dict[str, Any] | Unset = UNSET
        if not isinstance(self.oracle, Unset):
            oracle = self.oracle.to_dict()

        my_sql: dict[str, Any] | Unset = UNSET
        if not isinstance(self.my_sql, Unset):
            my_sql = self.my_sql.to_dict()

        postgre_sql: dict[str, Any] | Unset = UNSET
        if not isinstance(self.postgre_sql, Unset):
            postgre_sql = self.postgre_sql.to_dict()

        scripts: dict[str, Any] | Unset = UNSET
        if not isinstance(self.scripts, Unset):
            scripts = self.scripts.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "machineObject": machine_object,
                "vss": vss,
            }
        )
        if oracle is not UNSET:
            field_dict["oracle"] = oracle
        if my_sql is not UNSET:
            field_dict["mySql"] = my_sql
        if postgre_sql is not UNSET:
            field_dict["postgreSql"] = postgre_sql
        if scripts is not UNSET:
            field_dict["scripts"] = scripts

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.agent_backup_my_sql_settings_model import AgentBackupMySQLSettingsModel
        from ..models.agent_backup_oracle_settings_model import AgentBackupOracleSettingsModel
        from ..models.agent_object_model import AgentObjectModel
        from ..models.linux_agent_backup_script_settings_model import LinuxAgentBackupScriptSettingsModel
        from ..models.postgre_sql_settings_model import PostgreSQLSettingsModel

        d = dict(src_dict)
        machine_object = AgentObjectModel.from_dict(d.pop("machineObject"))

        vss = EApplicationSettingsVSS(d.pop("vss"))

        _oracle = d.pop("oracle", UNSET)
        oracle: AgentBackupOracleSettingsModel | Unset
        if isinstance(_oracle, Unset):
            oracle = UNSET
        else:
            oracle = AgentBackupOracleSettingsModel.from_dict(_oracle)

        _my_sql = d.pop("mySql", UNSET)
        my_sql: AgentBackupMySQLSettingsModel | Unset
        if isinstance(_my_sql, Unset):
            my_sql = UNSET
        else:
            my_sql = AgentBackupMySQLSettingsModel.from_dict(_my_sql)

        _postgre_sql = d.pop("postgreSql", UNSET)
        postgre_sql: PostgreSQLSettingsModel | Unset
        if isinstance(_postgre_sql, Unset):
            postgre_sql = UNSET
        else:
            postgre_sql = PostgreSQLSettingsModel.from_dict(_postgre_sql)

        _scripts = d.pop("scripts", UNSET)
        scripts: LinuxAgentBackupScriptSettingsModel | Unset
        if isinstance(_scripts, Unset):
            scripts = UNSET
        else:
            scripts = LinuxAgentBackupScriptSettingsModel.from_dict(_scripts)

        linux_agent_backup_application_settings_model = cls(
            machine_object=machine_object,
            vss=vss,
            oracle=oracle,
            my_sql=my_sql,
            postgre_sql=postgre_sql,
            scripts=scripts,
        )

        linux_agent_backup_application_settings_model.additional_properties = d
        return linux_agent_backup_application_settings_model

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
