from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_amazon_region_type import EAmazonRegionType
from ..types import UNSET, Unset

T = TypeVar("T", bound="AmazonS3ServerAccountModel")


@_attrs_define
class AmazonS3ServerAccountModel:
    """
    Attributes:
        friendly_name (str):
        credentials_id (UUID):
        region_type (EAmazonRegionType | Unset): AWS region type.
        region_id (str | Unset):
    """

    friendly_name: str
    credentials_id: UUID
    region_type: EAmazonRegionType | Unset = UNSET
    region_id: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        friendly_name = self.friendly_name

        credentials_id = str(self.credentials_id)

        region_type: str | Unset = UNSET
        if not isinstance(self.region_type, Unset):
            region_type = self.region_type.value

        region_id = self.region_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "friendlyName": friendly_name,
                "credentialsId": credentials_id,
            }
        )
        if region_type is not UNSET:
            field_dict["regionType"] = region_type
        if region_id is not UNSET:
            field_dict["regionId"] = region_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        friendly_name = d.pop("friendlyName")

        credentials_id = UUID(d.pop("credentialsId"))

        _region_type = d.pop("regionType", UNSET)
        region_type: EAmazonRegionType | Unset
        if isinstance(_region_type, Unset):
            region_type = UNSET
        else:
            region_type = EAmazonRegionType(_region_type)

        region_id = d.pop("regionId", UNSET)

        amazon_s3_server_account_model = cls(
            friendly_name=friendly_name,
            credentials_id=credentials_id,
            region_type=region_type,
            region_id=region_id,
        )

        amazon_s3_server_account_model.additional_properties = d
        return amazon_s3_server_account_model

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
