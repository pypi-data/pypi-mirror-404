from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AgentBackupMySQLSettingsModel")


@_attrs_define
class AgentBackupMySQLSettingsModel:
    """Application-aware processing settings for MySQL databases.

    Attributes:
        use_password_file (bool | Unset): If `true`, the Veeam Agent will use a password file to connect to the MySQL
            server.
        credentials_id (UUID | Unset): Credentials ID.
        password_file_path (str | Unset): Absolute path for the password file that the Veeam Agent uses to connect to
            the MySQL server.
    """

    use_password_file: bool | Unset = UNSET
    credentials_id: UUID | Unset = UNSET
    password_file_path: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        use_password_file = self.use_password_file

        credentials_id: str | Unset = UNSET
        if not isinstance(self.credentials_id, Unset):
            credentials_id = str(self.credentials_id)

        password_file_path = self.password_file_path

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if use_password_file is not UNSET:
            field_dict["usePasswordFile"] = use_password_file
        if credentials_id is not UNSET:
            field_dict["credentialsId"] = credentials_id
        if password_file_path is not UNSET:
            field_dict["passwordFilePath"] = password_file_path

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        use_password_file = d.pop("usePasswordFile", UNSET)

        _credentials_id = d.pop("credentialsId", UNSET)
        credentials_id: UUID | Unset
        if isinstance(_credentials_id, Unset):
            credentials_id = UNSET
        else:
            credentials_id = UUID(_credentials_id)

        password_file_path = d.pop("passwordFilePath", UNSET)

        agent_backup_my_sql_settings_model = cls(
            use_password_file=use_password_file,
            credentials_id=credentials_id,
            password_file_path=password_file_path,
        )

        agent_backup_my_sql_settings_model.additional_properties = d
        return agent_backup_my_sql_settings_model

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
