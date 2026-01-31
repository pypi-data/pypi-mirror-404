from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_azure_region_type import EAzureRegionType
from ..models.e_unstructured_data_server_type import EUnstructuredDataServerType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.azure_blob_server_processing_model import AzureBlobServerProcessingModel


T = TypeVar("T", bound="AzureBlobServerModel")


@_attrs_define
class AzureBlobServerModel:
    """Azure Blob storage.

    Attributes:
        type_ (EUnstructuredDataServerType): Type of unstructured data server.
        friendly_name (str): Friendly name which will be assigned to your object storage.
        credentials_id (UUID): ID of the credentials used to access your Azure Blob storage.
        id (UUID | Unset): ID of unstructured data server.
        region_type (EAzureRegionType | Unset): Microsoft Azure region.
        processing (AzureBlobServerProcessingModel | Unset): Processing settings for Azure Blob storage.
    """

    type_: EUnstructuredDataServerType
    friendly_name: str
    credentials_id: UUID
    id: UUID | Unset = UNSET
    region_type: EAzureRegionType | Unset = UNSET
    processing: AzureBlobServerProcessingModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        friendly_name = self.friendly_name

        credentials_id = str(self.credentials_id)

        id: str | Unset = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        region_type: str | Unset = UNSET
        if not isinstance(self.region_type, Unset):
            region_type = self.region_type.value

        processing: dict[str, Any] | Unset = UNSET
        if not isinstance(self.processing, Unset):
            processing = self.processing.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "friendlyName": friendly_name,
                "credentialsId": credentials_id,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if region_type is not UNSET:
            field_dict["regionType"] = region_type
        if processing is not UNSET:
            field_dict["processing"] = processing

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.azure_blob_server_processing_model import AzureBlobServerProcessingModel

        d = dict(src_dict)
        type_ = EUnstructuredDataServerType(d.pop("type"))

        friendly_name = d.pop("friendlyName")

        credentials_id = UUID(d.pop("credentialsId"))

        _id = d.pop("id", UNSET)
        id: UUID | Unset
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        _region_type = d.pop("regionType", UNSET)
        region_type: EAzureRegionType | Unset
        if isinstance(_region_type, Unset):
            region_type = UNSET
        else:
            region_type = EAzureRegionType(_region_type)

        _processing = d.pop("processing", UNSET)
        processing: AzureBlobServerProcessingModel | Unset
        if isinstance(_processing, Unset):
            processing = UNSET
        else:
            processing = AzureBlobServerProcessingModel.from_dict(_processing)

        azure_blob_server_model = cls(
            type_=type_,
            friendly_name=friendly_name,
            credentials_id=credentials_id,
            id=id,
            region_type=region_type,
            processing=processing,
        )

        azure_blob_server_model.additional_properties = d
        return azure_blob_server_model

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
