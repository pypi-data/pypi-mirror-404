from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.entra_id_resource import EntraIdResource
    from ..models.tenant_response import TenantResponse


T = TypeVar("T", bound="DeploymentConsumptionTenantResponse")


@_attrs_define
class DeploymentConsumptionTenantResponse:
    """
    Attributes:
        azure_tenant_id (str): Tenant ID assigned by Microsoft Entra ID.
        tenant_items (TenantResponse): Tenant items.
        tenant_consumption (EntraIdResource): Resource consumption.
    """

    azure_tenant_id: str
    tenant_items: TenantResponse
    tenant_consumption: EntraIdResource
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        azure_tenant_id = self.azure_tenant_id

        tenant_items = self.tenant_items.to_dict()

        tenant_consumption = self.tenant_consumption.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "azureTenantId": azure_tenant_id,
                "tenantItems": tenant_items,
                "tenantConsumption": tenant_consumption,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.entra_id_resource import EntraIdResource
        from ..models.tenant_response import TenantResponse

        d = dict(src_dict)
        azure_tenant_id = d.pop("azureTenantId")

        tenant_items = TenantResponse.from_dict(d.pop("tenantItems"))

        tenant_consumption = EntraIdResource.from_dict(d.pop("tenantConsumption"))

        deployment_consumption_tenant_response = cls(
            azure_tenant_id=azure_tenant_id,
            tenant_items=tenant_items,
            tenant_consumption=tenant_consumption,
        )

        deployment_consumption_tenant_response.additional_properties = d
        return deployment_consumption_tenant_response

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
