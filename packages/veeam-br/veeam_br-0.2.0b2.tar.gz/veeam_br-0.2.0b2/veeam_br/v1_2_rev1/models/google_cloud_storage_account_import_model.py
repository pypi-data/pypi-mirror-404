from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.cloud_credentials_import_model import CloudCredentialsImportModel
    from ..models.object_storage_connection_import_spec import ObjectStorageConnectionImportSpec


T = TypeVar("T", bound="GoogleCloudStorageAccountImportModel")


@_attrs_define
class GoogleCloudStorageAccountImportModel:
    """Account used to access the Google Cloud storage.

    Attributes:
        credentials (CloudCredentialsImportModel): Cloud credentials used for connection.
        region_id (str): ID of a region where the storage bucket is located.
        connection_settings (ObjectStorageConnectionImportSpec): Object storage connection settings.
    """

    credentials: CloudCredentialsImportModel
    region_id: str
    connection_settings: ObjectStorageConnectionImportSpec
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        credentials = self.credentials.to_dict()

        region_id = self.region_id

        connection_settings = self.connection_settings.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "credentials": credentials,
                "regionId": region_id,
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

        region_id = d.pop("regionId")

        connection_settings = ObjectStorageConnectionImportSpec.from_dict(d.pop("connectionSettings"))

        google_cloud_storage_account_import_model = cls(
            credentials=credentials,
            region_id=region_id,
            connection_settings=connection_settings,
        )

        google_cloud_storage_account_import_model.additional_properties = d
        return google_cloud_storage_account_import_model

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
