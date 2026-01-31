from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_azure_compute_credentials_deployment_type import EAzureComputeCredentialsDeploymentType
from ..models.e_azure_region_type import EAzureRegionType
from ..types import UNSET, Unset

T = TypeVar("T", bound="AzureComputeCloudCredentialsDeploymentModel")


@_attrs_define
class AzureComputeCloudCredentialsDeploymentModel:
    """Environment to which you restore workloads.

    Attributes:
        deployment_type (EAzureComputeCredentialsDeploymentType): Deployment type (global Microsoft Azure or Microsoft
            Azure Stack Hub).
        region (EAzureRegionType | Unset): Microsoft Azure region.
    """

    deployment_type: EAzureComputeCredentialsDeploymentType
    region: EAzureRegionType | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        deployment_type = self.deployment_type.value

        region: str | Unset = UNSET
        if not isinstance(self.region, Unset):
            region = self.region.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "deploymentType": deployment_type,
            }
        )
        if region is not UNSET:
            field_dict["region"] = region

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        deployment_type = EAzureComputeCredentialsDeploymentType(d.pop("deploymentType"))

        _region = d.pop("region", UNSET)
        region: EAzureRegionType | Unset
        if isinstance(_region, Unset):
            region = UNSET
        else:
            region = EAzureRegionType(_region)

        azure_compute_cloud_credentials_deployment_model = cls(
            deployment_type=deployment_type,
            region=region,
        )

        azure_compute_cloud_credentials_deployment_model.additional_properties = d
        return azure_compute_cloud_credentials_deployment_model

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
