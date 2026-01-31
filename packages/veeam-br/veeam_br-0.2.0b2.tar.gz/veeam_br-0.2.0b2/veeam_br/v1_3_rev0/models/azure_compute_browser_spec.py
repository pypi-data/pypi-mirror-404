from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_cloud_service_type import ECloudServiceType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.azure_compute_browser_filters import AzureComputeBrowserFilters


T = TypeVar("T", bound="AzureComputeBrowserSpec")


@_attrs_define
class AzureComputeBrowserSpec:
    """Azure compute account settings.

    Attributes:
        credentials_id (UUID): ID of the object storage account (for browsing either storage or compute infrastructure).
        service_type (ECloudServiceType): Type of cloud service.
        filters (AzureComputeBrowserFilters | Unset): Azure compute hierarchy filters. Using the filters reduces not
            only the number of records in the response body but also the response time.
    """

    credentials_id: UUID
    service_type: ECloudServiceType
    filters: AzureComputeBrowserFilters | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        credentials_id = str(self.credentials_id)

        service_type = self.service_type.value

        filters: dict[str, Any] | Unset = UNSET
        if not isinstance(self.filters, Unset):
            filters = self.filters.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "credentialsId": credentials_id,
                "serviceType": service_type,
            }
        )
        if filters is not UNSET:
            field_dict["filters"] = filters

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.azure_compute_browser_filters import AzureComputeBrowserFilters

        d = dict(src_dict)
        credentials_id = UUID(d.pop("credentialsId"))

        service_type = ECloudServiceType(d.pop("serviceType"))

        _filters = d.pop("filters", UNSET)
        filters: AzureComputeBrowserFilters | Unset
        if isinstance(_filters, Unset):
            filters = UNSET
        else:
            filters = AzureComputeBrowserFilters.from_dict(_filters)

        azure_compute_browser_spec = cls(
            credentials_id=credentials_id,
            service_type=service_type,
            filters=filters,
        )

        azure_compute_browser_spec.additional_properties = d
        return azure_compute_browser_spec

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
