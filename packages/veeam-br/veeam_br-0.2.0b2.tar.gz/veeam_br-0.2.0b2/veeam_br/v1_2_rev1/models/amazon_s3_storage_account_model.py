from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_amazon_region_type import EAmazonRegionType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.object_storage_connection_model import ObjectStorageConnectionModel


T = TypeVar("T", bound="AmazonS3StorageAccountModel")


@_attrs_define
class AmazonS3StorageAccountModel:
    """Account used to access the Amazon S3 storage.

    Attributes:
        credentials_id (UUID): ID of the cloud credentials record.
        region_type (EAmazonRegionType): AWS region type.
        connection_settings (ObjectStorageConnectionModel | Unset): Object storage connection settings.
    """

    credentials_id: UUID
    region_type: EAmazonRegionType
    connection_settings: ObjectStorageConnectionModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        credentials_id = str(self.credentials_id)

        region_type = self.region_type.value

        connection_settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.connection_settings, Unset):
            connection_settings = self.connection_settings.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "credentialsId": credentials_id,
                "regionType": region_type,
            }
        )
        if connection_settings is not UNSET:
            field_dict["connectionSettings"] = connection_settings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.object_storage_connection_model import ObjectStorageConnectionModel

        d = dict(src_dict)
        credentials_id = UUID(d.pop("credentialsId"))

        region_type = EAmazonRegionType(d.pop("regionType"))

        _connection_settings = d.pop("connectionSettings", UNSET)
        connection_settings: ObjectStorageConnectionModel | Unset
        if isinstance(_connection_settings, Unset):
            connection_settings = UNSET
        else:
            connection_settings = ObjectStorageConnectionModel.from_dict(_connection_settings)

        amazon_s3_storage_account_model = cls(
            credentials_id=credentials_id,
            region_type=region_type,
            connection_settings=connection_settings,
        )

        amazon_s3_storage_account_model.additional_properties = d
        return amazon_s3_storage_account_model

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
