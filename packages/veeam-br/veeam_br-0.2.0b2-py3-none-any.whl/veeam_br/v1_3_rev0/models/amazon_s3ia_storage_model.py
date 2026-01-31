from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AmazonS3IAStorageModel")


@_attrs_define
class AmazonS3IAStorageModel:
    """Standard Infrequent Access.

    Attributes:
        is_enabled (bool | Unset): If `true`, Standard Infrequent Access is enabled.
        single_zone_enabled (bool | Unset): If `true`, Amazon S3 One Zone-Infrequent Access is enabled.
    """

    is_enabled: bool | Unset = UNSET
    single_zone_enabled: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        is_enabled = self.is_enabled

        single_zone_enabled = self.single_zone_enabled

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if is_enabled is not UNSET:
            field_dict["isEnabled"] = is_enabled
        if single_zone_enabled is not UNSET:
            field_dict["singleZoneEnabled"] = single_zone_enabled

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        is_enabled = d.pop("isEnabled", UNSET)

        single_zone_enabled = d.pop("singleZoneEnabled", UNSET)

        amazon_s3ia_storage_model = cls(
            is_enabled=is_enabled,
            single_zone_enabled=single_zone_enabled,
        )

        amazon_s3ia_storage_model.additional_properties = d
        return amazon_s3ia_storage_model

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
