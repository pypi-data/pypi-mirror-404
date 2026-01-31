from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_instance_license_workload_role import EInstanceLicenseWorkloadRole

T = TypeVar("T", bound="InstanceLicenseAssignmentSpec")


@_attrs_define
class InstanceLicenseAssignmentSpec:
    """Set the product edition for standalone Veeam Agents.

    Attributes:
        role (EInstanceLicenseWorkloadRole): Product edition that you want to assign to the standalone Veeam Agent.
    """

    role: EInstanceLicenseWorkloadRole
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        role = self.role.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "role": role,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        role = EInstanceLicenseWorkloadRole(d.pop("role"))

        instance_license_assignment_spec = cls(
            role=role,
        )

        instance_license_assignment_spec.additional_properties = d
        return instance_license_assignment_spec

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
