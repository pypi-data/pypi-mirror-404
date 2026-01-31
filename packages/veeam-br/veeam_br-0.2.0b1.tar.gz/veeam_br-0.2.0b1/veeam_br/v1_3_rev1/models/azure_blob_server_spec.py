from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_azure_region_type import EAzureRegionType
from ..models.e_unstructured_data_server_type import EUnstructuredDataServerType

if TYPE_CHECKING:
    from ..models.azure_blob_server_processing_model import AzureBlobServerProcessingModel


T = TypeVar("T", bound="AzureBlobServerSpec")


@_attrs_define
class AzureBlobServerSpec:
    """Settings for Microsoft Azure Blob storage.

    Attributes:
        type_ (EUnstructuredDataServerType): Type of unstructured data server.
        friendly_name (str): Friendly name of the repository.
        credentials_id (UUID): Credentials ID.
        region_type (EAzureRegionType): Microsoft Azure region.
        processing (AzureBlobServerProcessingModel): Processing settings for Microsoft Azure Blob storage.
    """

    type_: EUnstructuredDataServerType
    friendly_name: str
    credentials_id: UUID
    region_type: EAzureRegionType
    processing: AzureBlobServerProcessingModel
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        friendly_name = self.friendly_name

        credentials_id = str(self.credentials_id)

        region_type = self.region_type.value

        processing = self.processing.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "friendlyName": friendly_name,
                "credentialsId": credentials_id,
                "regionType": region_type,
                "processing": processing,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.azure_blob_server_processing_model import AzureBlobServerProcessingModel

        d = dict(src_dict)
        type_ = EUnstructuredDataServerType(d.pop("type"))

        friendly_name = d.pop("friendlyName")

        credentials_id = UUID(d.pop("credentialsId"))

        region_type = EAzureRegionType(d.pop("regionType"))

        processing = AzureBlobServerProcessingModel.from_dict(d.pop("processing"))

        azure_blob_server_spec = cls(
            type_=type_,
            friendly_name=friendly_name,
            credentials_id=credentials_id,
            region_type=region_type,
            processing=processing,
        )

        azure_blob_server_spec.additional_properties = d
        return azure_blob_server_spec

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
