from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="InstanceLicenseWorkloadModel")


@_attrs_define
class InstanceLicenseWorkloadModel:
    """Details on workload covered by instance licenses.

    Attributes:
        name (str): Protected workload name.
        host_name (str): Name of the host.
        used_instances_number (float): Number of consumed instances.
        type_ (str): Workload type.
        instance_id (UUID): Instance ID.
    """

    name: str
    host_name: str
    used_instances_number: float
    type_: str
    instance_id: UUID
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        host_name = self.host_name

        used_instances_number = self.used_instances_number

        type_ = self.type_

        instance_id = str(self.instance_id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "hostName": host_name,
                "usedInstancesNumber": used_instances_number,
                "type": type_,
                "instanceId": instance_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        host_name = d.pop("hostName")

        used_instances_number = d.pop("usedInstancesNumber")

        type_ = d.pop("type")

        instance_id = UUID(d.pop("instanceId"))

        instance_license_workload_model = cls(
            name=name,
            host_name=host_name,
            used_instances_number=used_instances_number,
            type_=type_,
            instance_id=instance_id,
        )

        instance_license_workload_model.additional_properties = d
        return instance_license_workload_model

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
