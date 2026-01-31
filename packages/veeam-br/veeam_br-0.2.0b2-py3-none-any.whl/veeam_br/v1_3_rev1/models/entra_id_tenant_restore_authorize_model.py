from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="EntraIdTenantRestoreAuthorizeModel")


@_attrs_define
class EntraIdTenantRestoreAuthorizeModel:
    """Authorization code exchange.

    Attributes:
        successful (bool): If `true`, the authorization code exchange was successful.
        error (str | Unset): Error summary.
        error_description (str | Unset): Error description.
        credentials_id (UUID | Unset): ID of the credentials record used for connection to the target tenant. The
            property is used only for delegated restore by a restore operator that does not have access to pre-saved
            credentials. To obtain the credentials, use the following requests&#58; <ol><li>Obtain a user code&#58; [Get
            User Code for Delegated Restore of Microsoft Entra ID
            Items](Restore#operation/GetEntraIdTenantRestoreDeviceCode).</li> <li>Use the user code to get the credentials
            ID&#58; [Get Credentials for Delegated Restore of Microsoft Entra ID
            Items](Restore#operation/GetEntraIdTenantRestoreDeviceCodeState).</li></ol>.
    """

    successful: bool
    error: str | Unset = UNSET
    error_description: str | Unset = UNSET
    credentials_id: UUID | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        successful = self.successful

        error = self.error

        error_description = self.error_description

        credentials_id: str | Unset = UNSET
        if not isinstance(self.credentials_id, Unset):
            credentials_id = str(self.credentials_id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "successful": successful,
            }
        )
        if error is not UNSET:
            field_dict["error"] = error
        if error_description is not UNSET:
            field_dict["errorDescription"] = error_description
        if credentials_id is not UNSET:
            field_dict["credentialsId"] = credentials_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        successful = d.pop("successful")

        error = d.pop("error", UNSET)

        error_description = d.pop("errorDescription", UNSET)

        _credentials_id = d.pop("credentialsId", UNSET)
        credentials_id: UUID | Unset
        if isinstance(_credentials_id, Unset):
            credentials_id = UNSET
        else:
            credentials_id = UUID(_credentials_id)

        entra_id_tenant_restore_authorize_model = cls(
            successful=successful,
            error=error,
            error_description=error_description,
            credentials_id=credentials_id,
        )

        entra_id_tenant_restore_authorize_model.additional_properties = d
        return entra_id_tenant_restore_authorize_model

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
