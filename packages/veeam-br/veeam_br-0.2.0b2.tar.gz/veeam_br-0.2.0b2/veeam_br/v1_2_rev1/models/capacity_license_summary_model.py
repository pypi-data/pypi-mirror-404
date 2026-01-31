from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.capacity_license_object_model import CapacityLicenseObjectModel
    from ..models.capacity_license_workload_model import CapacityLicenseWorkloadModel


T = TypeVar("T", bound="CapacityLicenseSummaryModel")


@_attrs_define
class CapacityLicenseSummaryModel:
    """Details on total and consumed capacity by workload.

    Attributes:
        licensed_capacity_tb (float): Total capacity provided by the license in TB.
        used_capacity_tb (float): Amount of consumed capacity in TB.
        objects (list[CapacityLicenseObjectModel] | Unset):
        workload (list[CapacityLicenseWorkloadModel] | Unset):
    """

    licensed_capacity_tb: float
    used_capacity_tb: float
    objects: list[CapacityLicenseObjectModel] | Unset = UNSET
    workload: list[CapacityLicenseWorkloadModel] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        licensed_capacity_tb = self.licensed_capacity_tb

        used_capacity_tb = self.used_capacity_tb

        objects: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.objects, Unset):
            objects = []
            for objects_item_data in self.objects:
                objects_item = objects_item_data.to_dict()
                objects.append(objects_item)

        workload: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.workload, Unset):
            workload = []
            for workload_item_data in self.workload:
                workload_item = workload_item_data.to_dict()
                workload.append(workload_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "licensedCapacityTb": licensed_capacity_tb,
                "usedCapacityTb": used_capacity_tb,
            }
        )
        if objects is not UNSET:
            field_dict["objects"] = objects
        if workload is not UNSET:
            field_dict["workload"] = workload

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.capacity_license_object_model import CapacityLicenseObjectModel
        from ..models.capacity_license_workload_model import CapacityLicenseWorkloadModel

        d = dict(src_dict)
        licensed_capacity_tb = d.pop("licensedCapacityTb")

        used_capacity_tb = d.pop("usedCapacityTb")

        _objects = d.pop("objects", UNSET)
        objects: list[CapacityLicenseObjectModel] | Unset = UNSET
        if _objects is not UNSET:
            objects = []
            for objects_item_data in _objects:
                objects_item = CapacityLicenseObjectModel.from_dict(objects_item_data)

                objects.append(objects_item)

        _workload = d.pop("workload", UNSET)
        workload: list[CapacityLicenseWorkloadModel] | Unset = UNSET
        if _workload is not UNSET:
            workload = []
            for workload_item_data in _workload:
                workload_item = CapacityLicenseWorkloadModel.from_dict(workload_item_data)

                workload.append(workload_item)

        capacity_license_summary_model = cls(
            licensed_capacity_tb=licensed_capacity_tb,
            used_capacity_tb=used_capacity_tb,
            objects=objects,
            workload=workload,
        )

        capacity_license_summary_model.additional_properties = d
        return capacity_license_summary_model

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
