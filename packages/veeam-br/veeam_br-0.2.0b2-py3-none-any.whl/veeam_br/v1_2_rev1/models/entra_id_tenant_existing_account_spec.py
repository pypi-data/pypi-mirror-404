from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.entra_id_tenant_authentication_spec import EntraIDTenantAuthenticationSpec


T = TypeVar("T", bound="EntraIDTenantExistingAccountSpec")


@_attrs_define
class EntraIDTenantExistingAccountSpec:
    """Existing Microsoft Entra ID app registration.

    Attributes:
        authentication (EntraIDTenantAuthenticationSpec): Authentication settings.
    """

    authentication: EntraIDTenantAuthenticationSpec
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        authentication = self.authentication.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "authentication": authentication,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.entra_id_tenant_authentication_spec import EntraIDTenantAuthenticationSpec

        d = dict(src_dict)
        authentication = EntraIDTenantAuthenticationSpec.from_dict(d.pop("authentication"))

        entra_id_tenant_existing_account_spec = cls(
            authentication=authentication,
        )

        entra_id_tenant_existing_account_spec.additional_properties = d
        return entra_id_tenant_existing_account_spec

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
