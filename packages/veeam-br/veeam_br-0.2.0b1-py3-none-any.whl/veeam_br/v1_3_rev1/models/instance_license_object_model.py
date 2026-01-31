from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="InstanceLicenseObjectModel")


@_attrs_define
class InstanceLicenseObjectModel:
    """Details on workloads covered by instance licenses.

    Attributes:
        type_ (str): Type of a protected workload.
        count (int): Number of protected workloads.
        multiplier (float): Consumed instance multiplier.
        used_instances_number (float): Number of consumed instances.
    """

    type_: str
    count: int
    multiplier: float
    used_instances_number: float
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_

        count = self.count

        multiplier = self.multiplier

        used_instances_number = self.used_instances_number

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "count": count,
                "multiplier": multiplier,
                "usedInstancesNumber": used_instances_number,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        type_ = d.pop("type")

        count = d.pop("count")

        multiplier = d.pop("multiplier")

        used_instances_number = d.pop("usedInstancesNumber")

        instance_license_object_model = cls(
            type_=type_,
            count=count,
            multiplier=multiplier,
            used_instances_number=used_instances_number,
        )

        instance_license_object_model.additional_properties = d
        return instance_license_object_model

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
