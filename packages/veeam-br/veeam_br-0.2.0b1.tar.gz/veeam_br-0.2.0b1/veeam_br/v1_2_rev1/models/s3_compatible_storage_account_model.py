from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.object_storage_connection_model import ObjectStorageConnectionModel


T = TypeVar("T", bound="S3CompatibleStorageAccountModel")


@_attrs_define
class S3CompatibleStorageAccountModel:
    """Account used to access the S3 compatible storage.

    Attributes:
        service_point (str): Endpoint address and port number of the storage.
        region_id (str): ID of a region where the storage is located.
        credentials_id (UUID): ID of a cloud credentials record used to access the storage.
        connection_settings (ObjectStorageConnectionModel | Unset): Object storage connection settings.
    """

    service_point: str
    region_id: str
    credentials_id: UUID
    connection_settings: ObjectStorageConnectionModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        service_point = self.service_point

        region_id = self.region_id

        credentials_id = str(self.credentials_id)

        connection_settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.connection_settings, Unset):
            connection_settings = self.connection_settings.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "servicePoint": service_point,
                "regionId": region_id,
                "credentialsId": credentials_id,
            }
        )
        if connection_settings is not UNSET:
            field_dict["connectionSettings"] = connection_settings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.object_storage_connection_model import ObjectStorageConnectionModel

        d = dict(src_dict)
        service_point = d.pop("servicePoint")

        region_id = d.pop("regionId")

        credentials_id = UUID(d.pop("credentialsId"))

        _connection_settings = d.pop("connectionSettings", UNSET)
        connection_settings: ObjectStorageConnectionModel | Unset
        if isinstance(_connection_settings, Unset):
            connection_settings = UNSET
        else:
            connection_settings = ObjectStorageConnectionModel.from_dict(_connection_settings)

        s3_compatible_storage_account_model = cls(
            service_point=service_point,
            region_id=region_id,
            credentials_id=credentials_id,
            connection_settings=connection_settings,
        )

        s3_compatible_storage_account_model.additional_properties = d
        return s3_compatible_storage_account_model

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
