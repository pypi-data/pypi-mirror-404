from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AgentBackupSharepointSettingsModel")


@_attrs_define
class AgentBackupSharepointSettingsModel:
    """Application-aware processing settings for Microsoft SharePoint databases.

    Attributes:
        use_guest_credentials (bool | Unset): If `true`, Veeam Backup & Replication uses credentials specified in the
            guest processing settings.
        credentials_id (UUID | Unset): ID of the credentials record that is used if `useGuestCredentials` is *false*.
    """

    use_guest_credentials: bool | Unset = UNSET
    credentials_id: UUID | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        use_guest_credentials = self.use_guest_credentials

        credentials_id: str | Unset = UNSET
        if not isinstance(self.credentials_id, Unset):
            credentials_id = str(self.credentials_id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if use_guest_credentials is not UNSET:
            field_dict["useGuestCredentials"] = use_guest_credentials
        if credentials_id is not UNSET:
            field_dict["credentialsId"] = credentials_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        use_guest_credentials = d.pop("useGuestCredentials", UNSET)

        _credentials_id = d.pop("credentialsId", UNSET)
        credentials_id: UUID | Unset
        if isinstance(_credentials_id, Unset):
            credentials_id = UNSET
        else:
            credentials_id = UUID(_credentials_id)

        agent_backup_sharepoint_settings_model = cls(
            use_guest_credentials=use_guest_credentials,
            credentials_id=credentials_id,
        )

        agent_backup_sharepoint_settings_model.additional_properties = d
        return agent_backup_sharepoint_settings_model

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
