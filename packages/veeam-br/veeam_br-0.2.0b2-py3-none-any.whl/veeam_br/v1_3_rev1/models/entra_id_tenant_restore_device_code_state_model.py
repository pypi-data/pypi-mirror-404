from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_entra_id_tenant_restore_device_code_status import EEntraIdTenantRestoreDeviceCodeStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="EntraIdTenantRestoreDeviceCodeStateModel")


@_attrs_define
class EntraIdTenantRestoreDeviceCodeStateModel:
    """User code state.

    Attributes:
        credentials_id (UUID | Unset): Credentials ID required for delegated restore of Microsoft Entra ID items.
        error_message (str | Unset): Error message.
        status (EEntraIdTenantRestoreDeviceCodeStatus | Unset): Request status.
        username (str | Unset): User name.
    """

    credentials_id: UUID | Unset = UNSET
    error_message: str | Unset = UNSET
    status: EEntraIdTenantRestoreDeviceCodeStatus | Unset = UNSET
    username: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        credentials_id: str | Unset = UNSET
        if not isinstance(self.credentials_id, Unset):
            credentials_id = str(self.credentials_id)

        error_message = self.error_message

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        username = self.username

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if credentials_id is not UNSET:
            field_dict["credentialsId"] = credentials_id
        if error_message is not UNSET:
            field_dict["errorMessage"] = error_message
        if status is not UNSET:
            field_dict["status"] = status
        if username is not UNSET:
            field_dict["username"] = username

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _credentials_id = d.pop("credentialsId", UNSET)
        credentials_id: UUID | Unset
        if isinstance(_credentials_id, Unset):
            credentials_id = UNSET
        else:
            credentials_id = UUID(_credentials_id)

        error_message = d.pop("errorMessage", UNSET)

        _status = d.pop("status", UNSET)
        status: EEntraIdTenantRestoreDeviceCodeStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = EEntraIdTenantRestoreDeviceCodeStatus(_status)

        username = d.pop("username", UNSET)

        entra_id_tenant_restore_device_code_state_model = cls(
            credentials_id=credentials_id,
            error_message=error_message,
            status=status,
            username=username,
        )

        entra_id_tenant_restore_device_code_state_model.additional_properties = d
        return entra_id_tenant_restore_device_code_state_model

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
