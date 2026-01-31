from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_cloud_credentials_type import ECloudCredentialsType

T = TypeVar("T", bound="AzureComputeCloudNativeApplicationModel")


@_attrs_define
class AzureComputeCloudNativeApplicationModel:
    """Microsoft Entra ID application verification details.

    Attributes:
        type_ (ECloudCredentialsType): Cloud credentials type.
        application_id (str): Client ID assigned to the Microsoft Entra ID application.
        secret (str): Client secret assigned to the Microsoft Entra ID application.
        tenant_id (str): ID of a tenant where the Microsoft Entra ID application is registered.
    """

    type_: ECloudCredentialsType
    application_id: str
    secret: str
    tenant_id: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        application_id = self.application_id

        secret = self.secret

        tenant_id = self.tenant_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "applicationId": application_id,
                "secret": secret,
                "tenantId": tenant_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        type_ = ECloudCredentialsType(d.pop("type"))

        application_id = d.pop("applicationId")

        secret = d.pop("secret")

        tenant_id = d.pop("tenantId")

        azure_compute_cloud_native_application_model = cls(
            type_=type_,
            application_id=application_id,
            secret=secret,
            tenant_id=tenant_id,
        )

        azure_compute_cloud_native_application_model.additional_properties = d
        return azure_compute_cloud_native_application_model

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
