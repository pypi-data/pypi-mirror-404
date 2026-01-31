from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="EntraIdTenantRestoreAuthorizeSpec")


@_attrs_define
class EntraIdTenantRestoreAuthorizeSpec:
    """Settings for authorization code exchange.

    Attributes:
        session_id (UUID): Mount session ID.
        code (str | Unset): Authorization code returned by the authorization provider.
        state (str | Unset): State string returned by the authorization provider.
        error (str | Unset): Error summary.
        error_description (str | Unset): Error description.
    """

    session_id: UUID
    code: str | Unset = UNSET
    state: str | Unset = UNSET
    error: str | Unset = UNSET
    error_description: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        session_id = str(self.session_id)

        code = self.code

        state = self.state

        error = self.error

        error_description = self.error_description

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "sessionId": session_id,
            }
        )
        if code is not UNSET:
            field_dict["code"] = code
        if state is not UNSET:
            field_dict["state"] = state
        if error is not UNSET:
            field_dict["error"] = error
        if error_description is not UNSET:
            field_dict["errorDescription"] = error_description

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        session_id = UUID(d.pop("sessionId"))

        code = d.pop("code", UNSET)

        state = d.pop("state", UNSET)

        error = d.pop("error", UNSET)

        error_description = d.pop("errorDescription", UNSET)

        entra_id_tenant_restore_authorize_spec = cls(
            session_id=session_id,
            code=code,
            state=state,
            error=error,
            error_description=error_description,
        )

        entra_id_tenant_restore_authorize_spec.additional_properties = d
        return entra_id_tenant_restore_authorize_spec

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
