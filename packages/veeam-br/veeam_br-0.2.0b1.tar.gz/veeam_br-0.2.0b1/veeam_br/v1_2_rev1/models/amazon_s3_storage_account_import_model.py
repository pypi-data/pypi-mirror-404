from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_amazon_region_type import EAmazonRegionType

if TYPE_CHECKING:
    from ..models.cloud_credentials_import_model import CloudCredentialsImportModel
    from ..models.object_storage_connection_import_spec import ObjectStorageConnectionImportSpec


T = TypeVar("T", bound="AmazonS3StorageAccountImportModel")


@_attrs_define
class AmazonS3StorageAccountImportModel:
    """Account used to access the Amazon S3 storage.

    Attributes:
        credentials (CloudCredentialsImportModel): Cloud credentials used for connection.
        region_type (EAmazonRegionType): AWS region type.
        connection_settings (ObjectStorageConnectionImportSpec): Object storage connection settings.
    """

    credentials: CloudCredentialsImportModel
    region_type: EAmazonRegionType
    connection_settings: ObjectStorageConnectionImportSpec
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        credentials = self.credentials.to_dict()

        region_type = self.region_type.value

        connection_settings = self.connection_settings.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "credentials": credentials,
                "regionType": region_type,
                "connectionSettings": connection_settings,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.cloud_credentials_import_model import CloudCredentialsImportModel
        from ..models.object_storage_connection_import_spec import ObjectStorageConnectionImportSpec

        d = dict(src_dict)
        credentials = CloudCredentialsImportModel.from_dict(d.pop("credentials"))

        region_type = EAmazonRegionType(d.pop("regionType"))

        connection_settings = ObjectStorageConnectionImportSpec.from_dict(d.pop("connectionSettings"))

        amazon_s3_storage_account_import_model = cls(
            credentials=credentials,
            region_type=region_type,
            connection_settings=connection_settings,
        )

        amazon_s3_storage_account_import_model.additional_properties = d
        return amazon_s3_storage_account_import_model

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
