from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_capacity_license_object_type import ECapacityLicenseObjectType

T = TypeVar("T", bound="CapacityLicenseObjectModel")


@_attrs_define
class CapacityLicenseObjectModel:
    """Type of unstructured data source and the capacity it consumes.

    Attributes:
        type_ (ECapacityLicenseObjectType): Type of unstructured data source.
        used_capacity_tb (float): Amount of consumed capacity in TB.
    """

    type_: ECapacityLicenseObjectType
    used_capacity_tb: float
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        used_capacity_tb = self.used_capacity_tb

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "usedCapacityTb": used_capacity_tb,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        type_ = ECapacityLicenseObjectType(d.pop("type"))

        used_capacity_tb = d.pop("usedCapacityTb")

        capacity_license_object_model = cls(
            type_=type_,
            used_capacity_tb=used_capacity_tb,
        )

        capacity_license_object_model.additional_properties = d
        return capacity_license_object_model

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
