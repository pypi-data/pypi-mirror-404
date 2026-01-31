from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.deployment_consumption_tenant_response import DeploymentConsumptionTenantResponse
    from ..models.entra_id_plugin_settings import EntraIDPluginSettings
    from ..models.entra_id_resource import EntraIdResource
    from ..models.issue import Issue


T = TypeVar("T", bound="DeploymentConsumptionResponse")


@_attrs_define
class DeploymentConsumptionResponse:
    """
    Attributes:
        instance_id (str): ID of an instance where Veeam Backup & Replication is deployed.
        tenants (list[DeploymentConsumptionTenantResponse]): Array of tenants added to the backup server.
        instance_consumption (EntraIdResource): Resource consumption.
        issue (Issue): Issue status.
        entra_id_plugin_settings (EntraIDPluginSettings):
        template_id (str | Unset):
    """

    instance_id: str
    tenants: list[DeploymentConsumptionTenantResponse]
    instance_consumption: EntraIdResource
    issue: Issue
    entra_id_plugin_settings: EntraIDPluginSettings
    template_id: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        instance_id = self.instance_id

        tenants = []
        for tenants_item_data in self.tenants:
            tenants_item = tenants_item_data.to_dict()
            tenants.append(tenants_item)

        instance_consumption = self.instance_consumption.to_dict()

        issue = self.issue.to_dict()

        entra_id_plugin_settings = self.entra_id_plugin_settings.to_dict()

        template_id = self.template_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "instanceId": instance_id,
                "tenants": tenants,
                "instanceConsumption": instance_consumption,
                "issue": issue,
                "entraIdPluginSettings": entra_id_plugin_settings,
            }
        )
        if template_id is not UNSET:
            field_dict["templateId"] = template_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.deployment_consumption_tenant_response import DeploymentConsumptionTenantResponse
        from ..models.entra_id_plugin_settings import EntraIDPluginSettings
        from ..models.entra_id_resource import EntraIdResource
        from ..models.issue import Issue

        d = dict(src_dict)
        instance_id = d.pop("instanceId")

        tenants = []
        _tenants = d.pop("tenants")
        for tenants_item_data in _tenants:
            tenants_item = DeploymentConsumptionTenantResponse.from_dict(tenants_item_data)

            tenants.append(tenants_item)

        instance_consumption = EntraIdResource.from_dict(d.pop("instanceConsumption"))

        issue = Issue.from_dict(d.pop("issue"))

        entra_id_plugin_settings = EntraIDPluginSettings.from_dict(d.pop("entraIdPluginSettings"))

        template_id = d.pop("templateId", UNSET)

        deployment_consumption_response = cls(
            instance_id=instance_id,
            tenants=tenants,
            instance_consumption=instance_consumption,
            issue=issue,
            entra_id_plugin_settings=entra_id_plugin_settings,
            template_id=template_id,
        )

        deployment_consumption_response.additional_properties = d
        return deployment_consumption_response

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
