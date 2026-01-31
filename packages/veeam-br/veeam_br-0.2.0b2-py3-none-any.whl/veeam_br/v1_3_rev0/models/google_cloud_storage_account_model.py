from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.object_storage_connection_model import ObjectStorageConnectionModel


T = TypeVar("T", bound="GoogleCloudStorageAccountModel")


@_attrs_define
class GoogleCloudStorageAccountModel:
    """Account used to access the Google Cloud storage.

    Attributes:
        credentials_id (UUID): ID of a cloud credentials record used to access the storage.
        region_id (str): ID of a region where the storage bucket is located.
        connection_settings (ObjectStorageConnectionModel): Object storage connection settings.
    """

    credentials_id: UUID
    region_id: str
    connection_settings: ObjectStorageConnectionModel
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        credentials_id = str(self.credentials_id)

        region_id = self.region_id

        connection_settings = self.connection_settings.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "credentialsId": credentials_id,
                "regionId": region_id,
                "connectionSettings": connection_settings,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.object_storage_connection_model import ObjectStorageConnectionModel

        d = dict(src_dict)
        credentials_id = UUID(d.pop("credentialsId"))

        region_id = d.pop("regionId")

        connection_settings = ObjectStorageConnectionModel.from_dict(d.pop("connectionSettings"))

        google_cloud_storage_account_model = cls(
            credentials_id=credentials_id,
            region_id=region_id,
            connection_settings=connection_settings,
        )

        google_cloud_storage_account_model.additional_properties = d
        return google_cloud_storage_account_model

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
