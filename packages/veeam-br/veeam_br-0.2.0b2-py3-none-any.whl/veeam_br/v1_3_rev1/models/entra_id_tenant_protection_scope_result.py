from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_entra_id_tenant_resource import EEntraIdTenantResource

T = TypeVar("T", bound="EntraIdTenantProtectionScopeResult")


@_attrs_define
class EntraIdTenantProtectionScopeResult:
    """Microsoft Entra ID protection scope.

    Attributes:
        tenant_resources (list[EEntraIdTenantResource]): Array of Microsoft Entra ID tenant resources.
    """

    tenant_resources: list[EEntraIdTenantResource]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        tenant_resources = []
        for tenant_resources_item_data in self.tenant_resources:
            tenant_resources_item = tenant_resources_item_data.value
            tenant_resources.append(tenant_resources_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "tenantResources": tenant_resources,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        tenant_resources = []
        _tenant_resources = d.pop("tenantResources")
        for tenant_resources_item_data in _tenant_resources:
            tenant_resources_item = EEntraIdTenantResource(tenant_resources_item_data)

            tenant_resources.append(tenant_resources_item)

        entra_id_tenant_protection_scope_result = cls(
            tenant_resources=tenant_resources,
        )

        entra_id_tenant_protection_scope_result.additional_properties = d
        return entra_id_tenant_protection_scope_result

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
