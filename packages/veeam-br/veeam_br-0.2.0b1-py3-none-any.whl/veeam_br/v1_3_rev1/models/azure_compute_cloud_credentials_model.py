from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.e_cloud_credentials_type import ECloudCredentialsType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.azure_compute_cloud_credentials_deployment_model import AzureComputeCloudCredentialsDeploymentModel
    from ..models.azure_compute_cloud_credentials_subscription_model import (
        AzureComputeCloudCredentialsSubscriptionModel,
    )


T = TypeVar("T", bound="AzureComputeCloudCredentialsModel")


@_attrs_define
class AzureComputeCloudCredentialsModel:
    """Credentials for Microsoft Azure compute account.

    Attributes:
        id (UUID): ID of the cloud credentials record.
        type_ (ECloudCredentialsType): Cloud credentials type.
        connection_name (str): Name under which the cloud credentials record is shown in Veeam Backup & Replication.
        deployment (AzureComputeCloudCredentialsDeploymentModel): Environment to which you restore workloads.
        subscription (AzureComputeCloudCredentialsSubscriptionModel): Subscription information for Microsoft Azure
            compute account.
        description (str | Unset): Description of the cloud credentials record.
        last_modified (datetime.datetime | Unset): Date and time the credential record was last modified.
        unique_id (str | Unset): Unique ID that identifies the cloud credentials record.
    """

    id: UUID
    type_: ECloudCredentialsType
    connection_name: str
    deployment: AzureComputeCloudCredentialsDeploymentModel
    subscription: AzureComputeCloudCredentialsSubscriptionModel
    description: str | Unset = UNSET
    last_modified: datetime.datetime | Unset = UNSET
    unique_id: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        type_ = self.type_.value

        connection_name = self.connection_name

        deployment = self.deployment.to_dict()

        subscription = self.subscription.to_dict()

        description = self.description

        last_modified: str | Unset = UNSET
        if not isinstance(self.last_modified, Unset):
            last_modified = self.last_modified.isoformat()

        unique_id = self.unique_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "type": type_,
                "connectionName": connection_name,
                "deployment": deployment,
                "subscription": subscription,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if last_modified is not UNSET:
            field_dict["lastModified"] = last_modified
        if unique_id is not UNSET:
            field_dict["uniqueId"] = unique_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.azure_compute_cloud_credentials_deployment_model import (
            AzureComputeCloudCredentialsDeploymentModel,
        )
        from ..models.azure_compute_cloud_credentials_subscription_model import (
            AzureComputeCloudCredentialsSubscriptionModel,
        )

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        type_ = ECloudCredentialsType(d.pop("type"))

        connection_name = d.pop("connectionName")

        deployment = AzureComputeCloudCredentialsDeploymentModel.from_dict(d.pop("deployment"))

        subscription = AzureComputeCloudCredentialsSubscriptionModel.from_dict(d.pop("subscription"))

        description = d.pop("description", UNSET)

        _last_modified = d.pop("lastModified", UNSET)
        last_modified: datetime.datetime | Unset
        if isinstance(_last_modified, Unset):
            last_modified = UNSET
        else:
            last_modified = isoparse(_last_modified)

        unique_id = d.pop("uniqueId", UNSET)

        azure_compute_cloud_credentials_model = cls(
            id=id,
            type_=type_,
            connection_name=connection_name,
            deployment=deployment,
            subscription=subscription,
            description=description,
            last_modified=last_modified,
            unique_id=unique_id,
        )

        azure_compute_cloud_credentials_model.additional_properties = d
        return azure_compute_cloud_credentials_model

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
