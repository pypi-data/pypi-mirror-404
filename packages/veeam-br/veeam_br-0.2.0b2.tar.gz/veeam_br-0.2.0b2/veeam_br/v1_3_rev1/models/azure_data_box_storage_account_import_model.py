from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.cloud_credentials_import_model import CloudCredentialsImportModel
    from ..models.object_storage_connection_import_spec import ObjectStorageConnectionImportSpec


T = TypeVar("T", bound="AzureDataBoxStorageAccountImportModel")


@_attrs_define
class AzureDataBoxStorageAccountImportModel:
    """Account used to access the Microsoft Azure Data Box storage.

    Attributes:
        service_endpoint (str): Service endpoint address of the Microsoft Azure Data Box device.
        credentials (CloudCredentialsImportModel): Cloud credentials used for connection.
        connection_settings (ObjectStorageConnectionImportSpec): Object storage connection settings.
    """

    service_endpoint: str
    credentials: CloudCredentialsImportModel
    connection_settings: ObjectStorageConnectionImportSpec
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        service_endpoint = self.service_endpoint

        credentials = self.credentials.to_dict()

        connection_settings = self.connection_settings.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "serviceEndpoint": service_endpoint,
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
        service_endpoint = d.pop("serviceEndpoint")

        credentials = CloudCredentialsImportModel.from_dict(d.pop("credentials"))

        connection_settings = ObjectStorageConnectionImportSpec.from_dict(d.pop("connectionSettings"))

        azure_data_box_storage_account_import_model = cls(
            service_endpoint=service_endpoint,
            credentials=credentials,
            connection_settings=connection_settings,
        )

        azure_data_box_storage_account_import_model.additional_properties = d
        return azure_data_box_storage_account_import_model

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
