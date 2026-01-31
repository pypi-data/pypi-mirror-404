from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="EntraIdTenantRestoreDeviceCodeModel")


@_attrs_define
class EntraIdTenantRestoreDeviceCodeModel:
    """Device code settings.

    Attributes:
        user_code (str): User code.
        device_code (str): Device code.
        verification_url (str): Verification URL (redirect URI).
        message (str | Unset): Message text.
        client_id (str | Unset): Application (client) ID.
        expires_on (datetime.datetime | Unset): Expiration date and time of the verification code.
    """

    user_code: str
    device_code: str
    verification_url: str
    message: str | Unset = UNSET
    client_id: str | Unset = UNSET
    expires_on: datetime.datetime | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        user_code = self.user_code

        device_code = self.device_code

        verification_url = self.verification_url

        message = self.message

        client_id = self.client_id

        expires_on: str | Unset = UNSET
        if not isinstance(self.expires_on, Unset):
            expires_on = self.expires_on.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "userCode": user_code,
                "deviceCode": device_code,
                "verificationUrl": verification_url,
            }
        )
        if message is not UNSET:
            field_dict["message"] = message
        if client_id is not UNSET:
            field_dict["clientId"] = client_id
        if expires_on is not UNSET:
            field_dict["expiresOn"] = expires_on

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        user_code = d.pop("userCode")

        device_code = d.pop("deviceCode")

        verification_url = d.pop("verificationUrl")

        message = d.pop("message", UNSET)

        client_id = d.pop("clientId", UNSET)

        _expires_on = d.pop("expiresOn", UNSET)
        expires_on: datetime.datetime | Unset
        if isinstance(_expires_on, Unset):
            expires_on = UNSET
        else:
            expires_on = isoparse(_expires_on)

        entra_id_tenant_restore_device_code_model = cls(
            user_code=user_code,
            device_code=device_code,
            verification_url=verification_url,
            message=message,
            client_id=client_id,
            expires_on=expires_on,
        )

        entra_id_tenant_restore_device_code_model.additional_properties = d
        return entra_id_tenant_restore_device_code_model

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
