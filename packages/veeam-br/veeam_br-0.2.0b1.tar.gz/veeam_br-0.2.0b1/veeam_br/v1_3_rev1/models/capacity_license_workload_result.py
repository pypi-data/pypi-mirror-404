from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.capacity_license_workload_model import CapacityLicenseWorkloadModel


T = TypeVar("T", bound="CapacityLicenseWorkloadResult")


@_attrs_define
class CapacityLicenseWorkloadResult:
    """Details on unstructured data workloads.

    Attributes:
        workloads (list[CapacityLicenseWorkloadModel]): Array of protected unstructured data workloads.
    """

    workloads: list[CapacityLicenseWorkloadModel]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        workloads = []
        for workloads_item_data in self.workloads:
            workloads_item = workloads_item_data.to_dict()
            workloads.append(workloads_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "workloads": workloads,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.capacity_license_workload_model import CapacityLicenseWorkloadModel

        d = dict(src_dict)
        workloads = []
        _workloads = d.pop("workloads")
        for workloads_item_data in _workloads:
            workloads_item = CapacityLicenseWorkloadModel.from_dict(workloads_item_data)

            workloads.append(workloads_item)

        capacity_license_workload_result = cls(
            workloads=workloads,
        )

        capacity_license_workload_result.additional_properties = d
        return capacity_license_workload_result

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
