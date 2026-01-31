from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.cloud_credentials_import_model import CloudCredentialsImportModel
    from ..models.object_storage_connection_import_spec import ObjectStorageConnectionImportSpec


T = TypeVar("T", bound="S3CompatibleStorageAccountImportModel")


@_attrs_define
class S3CompatibleStorageAccountImportModel:
    """Account used to access the S3 compatible storage.

    Attributes:
        service_point (str): Endpoint address of the storage.
        region_id (str): ID of a region where the storage is located.
        credentials (CloudCredentialsImportModel): Cloud credentials used for connection.
        connection_settings (ObjectStorageConnectionImportSpec): Object storage connection settings.
    """

    service_point: str
    region_id: str
    credentials: CloudCredentialsImportModel
    connection_settings: ObjectStorageConnectionImportSpec
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        service_point = self.service_point

        region_id = self.region_id

        credentials = self.credentials.to_dict()

        connection_settings = self.connection_settings.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "servicePoint": service_point,
                "regionId": region_id,
                "credentials": credentials,
                "connectionSettings": connection_settings,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.cloud_credentials_import_model import CloudCredentialsImportModel
        from ..models.object_storage_connection_import_spec import ObjectStorageConnectionImportSpec

        d = dict(src_dict)
        service_point = d.pop("servicePoint")

        region_id = d.pop("regionId")

        credentials = CloudCredentialsImportModel.from_dict(d.pop("credentials"))

        connection_settings = ObjectStorageConnectionImportSpec.from_dict(d.pop("connectionSettings"))

        s3_compatible_storage_account_import_model = cls(
            service_point=service_point,
            region_id=region_id,
            credentials=credentials,
            connection_settings=connection_settings,
        )

        s3_compatible_storage_account_import_model.additional_properties = d
        return s3_compatible_storage_account_import_model

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
