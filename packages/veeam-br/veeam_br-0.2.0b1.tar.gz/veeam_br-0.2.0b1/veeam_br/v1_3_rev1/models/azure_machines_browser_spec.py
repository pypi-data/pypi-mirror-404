from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_azure_region_type import EAzureRegionType
from ..models.e_protection_group_cloud_account_type import EProtectionGroupCloudAccountType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.azure_machines_browser_filters import AzureMachinesBrowserFilters


T = TypeVar("T", bound="AzureMachinesBrowserSpec")


@_attrs_define
class AzureMachinesBrowserSpec:
    """Microsoft Azure compute account settings.

    Attributes:
        service_type (EProtectionGroupCloudAccountType): Cloud account type.
        subscription_id (UUID): Filters compute resources by ID that Veeam Backup & Replication assigned to the
            Microsoft Azure subscription.
        region_type (EAzureRegionType): Microsoft Azure region.
        region (str): Filters compute resources by Microsoft Azure region name.
        filters (AzureMachinesBrowserFilters | Unset): Microsoft Azure machines filters. Using the filters reduces not
            only the number of records in the response body but also the response time.
    """

    service_type: EProtectionGroupCloudAccountType
    subscription_id: UUID
    region_type: EAzureRegionType
    region: str
    filters: AzureMachinesBrowserFilters | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        service_type = self.service_type.value

        subscription_id = str(self.subscription_id)

        region_type = self.region_type.value

        region = self.region

        filters: dict[str, Any] | Unset = UNSET
        if not isinstance(self.filters, Unset):
            filters = self.filters.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "serviceType": service_type,
                "subscriptionId": subscription_id,
                "regionType": region_type,
                "region": region,
            }
        )
        if filters is not UNSET:
            field_dict["filters"] = filters

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.azure_machines_browser_filters import AzureMachinesBrowserFilters

        d = dict(src_dict)
        service_type = EProtectionGroupCloudAccountType(d.pop("serviceType"))

        subscription_id = UUID(d.pop("subscriptionId"))

        region_type = EAzureRegionType(d.pop("regionType"))

        region = d.pop("region")

        _filters = d.pop("filters", UNSET)
        filters: AzureMachinesBrowserFilters | Unset
        if isinstance(_filters, Unset):
            filters = UNSET
        else:
            filters = AzureMachinesBrowserFilters.from_dict(_filters)

        azure_machines_browser_spec = cls(
            service_type=service_type,
            subscription_id=subscription_id,
            region_type=region_type,
            region=region,
            filters=filters,
        )

        azure_machines_browser_spec.additional_properties = d
        return azure_machines_browser_spec

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
