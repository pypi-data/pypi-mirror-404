from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.object_storage_connection_model import ObjectStorageConnectionModel


T = TypeVar("T", bound="WasabiCloudStorageAccountModel")


@_attrs_define
class WasabiCloudStorageAccountModel:
    """Account used to access the Wasabi Cloud storage.

    Attributes:
        region_id (str): ID of a region where the storage is located.
        credentials_id (UUID): ID of a cloud credentials record used to access the storage.
        connection_settings (ObjectStorageConnectionModel): Object storage connection settings.
    """

    region_id: str
    credentials_id: UUID
    connection_settings: ObjectStorageConnectionModel
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        region_id = self.region_id

        credentials_id = str(self.credentials_id)

        connection_settings = self.connection_settings.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "regionId": region_id,
                "credentialsId": credentials_id,
                "connectionSettings": connection_settings,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.object_storage_connection_model import ObjectStorageConnectionModel

        d = dict(src_dict)
        region_id = d.pop("regionId")

        credentials_id = UUID(d.pop("credentialsId"))

        connection_settings = ObjectStorageConnectionModel.from_dict(d.pop("connectionSettings"))

        wasabi_cloud_storage_account_model = cls(
            region_id=region_id,
            credentials_id=credentials_id,
            connection_settings=connection_settings,
        )

        wasabi_cloud_storage_account_model.additional_properties = d
        return wasabi_cloud_storage_account_model

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
