from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_capacity_license_object_type import ECapacityLicenseObjectType

T = TypeVar("T", bound="CapacityLicenseWorkloadModel")


@_attrs_define
class CapacityLicenseWorkloadModel:
    """Details on unstructured data workloads.

    Attributes:
        name (str): Name of the protected workload.
        used_capacity_tb (float): Amount of consumed capacity in TB.
        type_ (ECapacityLicenseObjectType): Type of unstructured data source.
        instance_id (UUID): Instance ID.
    """

    name: str
    used_capacity_tb: float
    type_: ECapacityLicenseObjectType
    instance_id: UUID
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        used_capacity_tb = self.used_capacity_tb

        type_ = self.type_.value

        instance_id = str(self.instance_id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "usedCapacityTb": used_capacity_tb,
                "type": type_,
                "instanceId": instance_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        used_capacity_tb = d.pop("usedCapacityTb")

        type_ = ECapacityLicenseObjectType(d.pop("type"))

        instance_id = UUID(d.pop("instanceId"))

        capacity_license_workload_model = cls(
            name=name,
            used_capacity_tb=used_capacity_tb,
            type_=type_,
            instance_id=instance_id,
        )

        capacity_license_workload_model.additional_properties = d
        return capacity_license_workload_model

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
