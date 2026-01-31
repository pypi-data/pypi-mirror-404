from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_cloud_credentials_type import ECloudCredentialsType
from ..types import UNSET, Unset

T = TypeVar("T", bound="CloudCredentialsSpec")


@_attrs_define
class CloudCredentialsSpec:
    """
    Attributes:
        type_ (ECloudCredentialsType): Cloud credentials type.
        description (str | Unset): Description of the cloud credentials record.
    """

    type_: ECloudCredentialsType
    description: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        description = self.description

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        type_ = ECloudCredentialsType(d.pop("type"))

        description = d.pop("description", UNSET)

        cloud_credentials_spec = cls(
            type_=type_,
            description=description,
        )

        cloud_credentials_spec.additional_properties = d
        return cloud_credentials_spec

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
