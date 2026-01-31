from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="S3CompatibleServerAccountModel")


@_attrs_define
class S3CompatibleServerAccountModel:
    """Account for S3 compatible object storage.

    Attributes:
        friendly_name (str): Friendly name which will be assigned to your object storage.
        credentials_id (UUID): ID of the credentials used to access your S3 compatible object storage.
        service_point (str | Unset): Service point address of your object storage.
        region_id (str | Unset): ID of a region where the storage is located.
    """

    friendly_name: str
    credentials_id: UUID
    service_point: str | Unset = UNSET
    region_id: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        friendly_name = self.friendly_name

        credentials_id = str(self.credentials_id)

        service_point = self.service_point

        region_id = self.region_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "friendlyName": friendly_name,
                "credentialsId": credentials_id,
            }
        )
        if service_point is not UNSET:
            field_dict["servicePoint"] = service_point
        if region_id is not UNSET:
            field_dict["regionId"] = region_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        friendly_name = d.pop("friendlyName")

        credentials_id = UUID(d.pop("credentialsId"))

        service_point = d.pop("servicePoint", UNSET)

        region_id = d.pop("regionId", UNSET)

        s3_compatible_server_account_model = cls(
            friendly_name=friendly_name,
            credentials_id=credentials_id,
            service_point=service_point,
            region_id=region_id,
        )

        s3_compatible_server_account_model.additional_properties = d
        return s3_compatible_server_account_model

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
