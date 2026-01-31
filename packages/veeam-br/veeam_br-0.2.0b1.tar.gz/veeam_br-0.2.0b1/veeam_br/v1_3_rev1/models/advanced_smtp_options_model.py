from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AdvancedSmtpOptionsModel")


@_attrs_define
class AdvancedSmtpOptionsModel:
    """Advanced global email notification settings.

    Attributes:
        port (int): Port number for the SMTP server.
        timeout_ms (int): Connection timeout for the SMTP server.
        ssl_enabled (bool): If `true`, secure connection for email operations is used.
        auth_required (bool): If `true`, the `credentialsId` credentials are used to connect to the SMTP server.
        credentials_id (UUID | Unset): ID of the credentials used to connect to the server.
    """

    port: int
    timeout_ms: int
    ssl_enabled: bool
    auth_required: bool
    credentials_id: UUID | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        port = self.port

        timeout_ms = self.timeout_ms

        ssl_enabled = self.ssl_enabled

        auth_required = self.auth_required

        credentials_id: str | Unset = UNSET
        if not isinstance(self.credentials_id, Unset):
            credentials_id = str(self.credentials_id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "port": port,
                "timeoutMs": timeout_ms,
                "SSLEnabled": ssl_enabled,
                "authRequired": auth_required,
            }
        )
        if credentials_id is not UNSET:
            field_dict["credentialsId"] = credentials_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        port = d.pop("port")

        timeout_ms = d.pop("timeoutMs")

        ssl_enabled = d.pop("SSLEnabled")

        auth_required = d.pop("authRequired")

        _credentials_id = d.pop("credentialsId", UNSET)
        credentials_id: UUID | Unset
        if isinstance(_credentials_id, Unset):
            credentials_id = UNSET
        else:
            credentials_id = UUID(_credentials_id)

        advanced_smtp_options_model = cls(
            port=port,
            timeout_ms=timeout_ms,
            ssl_enabled=ssl_enabled,
            auth_required=auth_required,
            credentials_id=credentials_id,
        )

        advanced_smtp_options_model.additional_properties = d
        return advanced_smtp_options_model

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
