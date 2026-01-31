from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="EntraIdTenantRestoreDeviceCodeStateSpec")


@_attrs_define
class EntraIdTenantRestoreDeviceCodeStateSpec:
    """
    Attributes:
        session_id (UUID): Mount session ID.
        user_code (str): User code. To get the code, use the [Get Microsoft Entra ID User Code for
            Restore](#tag/Restore/operation/GetEntraIdTenantRestoreDeviceCode) request.
    """

    session_id: UUID
    user_code: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        session_id = str(self.session_id)

        user_code = self.user_code

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "sessionId": session_id,
                "userCode": user_code,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        session_id = UUID(d.pop("sessionId"))

        user_code = d.pop("userCode")

        entra_id_tenant_restore_device_code_state_spec = cls(
            session_id=session_id,
            user_code=user_code,
        )

        entra_id_tenant_restore_device_code_state_spec.additional_properties = d
        return entra_id_tenant_restore_device_code_state_spec

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
