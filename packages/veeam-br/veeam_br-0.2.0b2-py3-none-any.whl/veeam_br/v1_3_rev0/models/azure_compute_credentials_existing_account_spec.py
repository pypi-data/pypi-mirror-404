from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.azure_compute_cloud_credentials_deployment_model import AzureComputeCloudCredentialsDeploymentModel
    from ..models.azure_compute_cloud_credentials_subscription_spec import AzureComputeCloudCredentialsSubscriptionSpec


T = TypeVar("T", bound="AzureComputeCredentialsExistingAccountSpec")


@_attrs_define
class AzureComputeCredentialsExistingAccountSpec:
    """Existing Microsoft Entra ID app registration.

    Attributes:
        deployment (AzureComputeCloudCredentialsDeploymentModel): Environment to which you restore workloads.
        subscription (AzureComputeCloudCredentialsSubscriptionSpec): Microsoft Azure compute account. For password-based
            authentication, specify client secret. For certificate-based authentication, specify certificate and password.
    """

    deployment: AzureComputeCloudCredentialsDeploymentModel
    subscription: AzureComputeCloudCredentialsSubscriptionSpec
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        deployment = self.deployment.to_dict()

        subscription = self.subscription.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "deployment": deployment,
                "subscription": subscription,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.azure_compute_cloud_credentials_deployment_model import (
            AzureComputeCloudCredentialsDeploymentModel,
        )
        from ..models.azure_compute_cloud_credentials_subscription_spec import (
            AzureComputeCloudCredentialsSubscriptionSpec,
        )

        d = dict(src_dict)
        deployment = AzureComputeCloudCredentialsDeploymentModel.from_dict(d.pop("deployment"))

        subscription = AzureComputeCloudCredentialsSubscriptionSpec.from_dict(d.pop("subscription"))

        azure_compute_credentials_existing_account_spec = cls(
            deployment=deployment,
            subscription=subscription,
        )

        azure_compute_credentials_existing_account_spec.additional_properties = d
        return azure_compute_credentials_existing_account_spec

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
