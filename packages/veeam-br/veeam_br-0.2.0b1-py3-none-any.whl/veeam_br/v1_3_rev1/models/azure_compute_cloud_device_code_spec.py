from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_azure_region_type import EAzureRegionType
from ..models.e_cloud_credentials_type import ECloudCredentialsType

T = TypeVar("T", bound="AzureComputeCloudDeviceCodeSpec")


@_attrs_define
class AzureComputeCloudDeviceCodeSpec:
    """Settings for getting verification code required to register a new Microsoft Entra ID application.

    Attributes:
        type_ (ECloudCredentialsType): Cloud credentials type.
        region (EAzureRegionType): Microsoft Azure region.
    """

    type_: ECloudCredentialsType
    region: EAzureRegionType
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        region = self.region.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "region": region,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        type_ = ECloudCredentialsType(d.pop("type"))

        region = EAzureRegionType(d.pop("region"))

        azure_compute_cloud_device_code_spec = cls(
            type_=type_,
            region=region,
        )

        azure_compute_cloud_device_code_spec.additional_properties = d
        return azure_compute_cloud_device_code_spec

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
