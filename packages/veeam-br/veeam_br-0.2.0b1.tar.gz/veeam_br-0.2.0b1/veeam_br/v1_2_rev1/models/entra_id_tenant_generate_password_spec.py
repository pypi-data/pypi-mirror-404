from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="EntraIdTenantGeneratePasswordSpec")


@_attrs_define
class EntraIdTenantGeneratePasswordSpec:
    """
    Attributes:
        passwords_count (int): Number of passwords.
    """

    passwords_count: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        passwords_count = self.passwords_count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "passwordsCount": passwords_count,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        passwords_count = d.pop("passwordsCount")

        entra_id_tenant_generate_password_spec = cls(
            passwords_count=passwords_count,
        )

        entra_id_tenant_generate_password_spec.additional_properties = d
        return entra_id_tenant_generate_password_spec

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
