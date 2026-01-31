from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="UserServiceAccountModeSpec")


@_attrs_define
class UserServiceAccountModeSpec:
    """Service account settings.

    Attributes:
        is_service_account_enable (bool): If `true`, the user or group is a service account.
    """

    is_service_account_enable: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        is_service_account_enable = self.is_service_account_enable

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "isServiceAccountEnable": is_service_account_enable,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        is_service_account_enable = d.pop("isServiceAccountEnable")

        user_service_account_mode_spec = cls(
            is_service_account_enable=is_service_account_enable,
        )

        user_service_account_mode_spec.additional_properties = d
        return user_service_account_mode_spec

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
