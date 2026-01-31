from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.entra_id_plugin_settings import EntraIDPluginSettings
    from ..models.entra_id_resource import EntraIdResource
    from ..models.issue import Issue
    from ..models.tenant_response import TenantResponse


T = TypeVar("T", bound="TenantLoadCalculatorResponse")


@_attrs_define
class TenantLoadCalculatorResponse:
    """Load calculator response.

    Attributes:
        instance_id (str): ID of an instance where Veeam Backup & Replication is deployed.
        azure_tenant_id (str): Tenant ID assigned by Microsoft Entra ID.
        tenant_items (TenantResponse): Tenant items.
        tenant_consumption (EntraIdResource): Resource consumption.
        issue (Issue): Issue status.
        instance_resource_left (EntraIdResource | Unset): Resource consumption.
        entra_id_plugin_settings (EntraIDPluginSettings | Unset): Settings for Microsoft Entra ID plug-in.
        template (str | Unset): Template.
    """

    instance_id: str
    azure_tenant_id: str
    tenant_items: TenantResponse
    tenant_consumption: EntraIdResource
    issue: Issue
    instance_resource_left: EntraIdResource | Unset = UNSET
    entra_id_plugin_settings: EntraIDPluginSettings | Unset = UNSET
    template: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        instance_id = self.instance_id

        azure_tenant_id = self.azure_tenant_id

        tenant_items = self.tenant_items.to_dict()

        tenant_consumption = self.tenant_consumption.to_dict()

        issue = self.issue.to_dict()

        instance_resource_left: dict[str, Any] | Unset = UNSET
        if not isinstance(self.instance_resource_left, Unset):
            instance_resource_left = self.instance_resource_left.to_dict()

        entra_id_plugin_settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.entra_id_plugin_settings, Unset):
            entra_id_plugin_settings = self.entra_id_plugin_settings.to_dict()

        template = self.template

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "instanceId": instance_id,
                "azureTenantId": azure_tenant_id,
                "tenantItems": tenant_items,
                "tenantConsumption": tenant_consumption,
                "issue": issue,
            }
        )
        if instance_resource_left is not UNSET:
            field_dict["instanceResourceLeft"] = instance_resource_left
        if entra_id_plugin_settings is not UNSET:
            field_dict["entraIdPluginSettings"] = entra_id_plugin_settings
        if template is not UNSET:
            field_dict["template"] = template

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.entra_id_plugin_settings import EntraIDPluginSettings
        from ..models.entra_id_resource import EntraIdResource
        from ..models.issue import Issue
        from ..models.tenant_response import TenantResponse

        d = dict(src_dict)
        instance_id = d.pop("instanceId")

        azure_tenant_id = d.pop("azureTenantId")

        tenant_items = TenantResponse.from_dict(d.pop("tenantItems"))

        tenant_consumption = EntraIdResource.from_dict(d.pop("tenantConsumption"))

        issue = Issue.from_dict(d.pop("issue"))

        _instance_resource_left = d.pop("instanceResourceLeft", UNSET)
        instance_resource_left: EntraIdResource | Unset
        if isinstance(_instance_resource_left, Unset):
            instance_resource_left = UNSET
        else:
            instance_resource_left = EntraIdResource.from_dict(_instance_resource_left)

        _entra_id_plugin_settings = d.pop("entraIdPluginSettings", UNSET)
        entra_id_plugin_settings: EntraIDPluginSettings | Unset
        if isinstance(_entra_id_plugin_settings, Unset):
            entra_id_plugin_settings = UNSET
        else:
            entra_id_plugin_settings = EntraIDPluginSettings.from_dict(_entra_id_plugin_settings)

        template = d.pop("template", UNSET)

        tenant_load_calculator_response = cls(
            instance_id=instance_id,
            azure_tenant_id=azure_tenant_id,
            tenant_items=tenant_items,
            tenant_consumption=tenant_consumption,
            issue=issue,
            instance_resource_left=instance_resource_left,
            entra_id_plugin_settings=entra_id_plugin_settings,
            template=template,
        )

        tenant_load_calculator_response.additional_properties = d
        return tenant_load_calculator_response

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
