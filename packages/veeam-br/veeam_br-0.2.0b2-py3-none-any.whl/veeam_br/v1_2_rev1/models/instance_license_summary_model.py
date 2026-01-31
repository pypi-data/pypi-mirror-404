from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.e_license_package_type import ELicensePackageType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.instance_license_object_model import InstanceLicenseObjectModel
    from ..models.instance_license_workload_model import InstanceLicenseWorkloadModel


T = TypeVar("T", bound="InstanceLicenseSummaryModel")


@_attrs_define
class InstanceLicenseSummaryModel:
    """Details on per-instance license consumption.

    Attributes:
        licensed_instances_number (float): Total number of instances that are available in the license scope.
        used_instances_number (float): Number of instances that have already been used.
        new_instances_number (float): Number of new instances, consumed for the first time within the current calendar
            month. New instances are counted separately and do not consume licenses in the current month.
        rental_instances_number (float): Number of consumed instances.
        objects (list[InstanceLicenseObjectModel] | Unset): Array of objects containing details on workloads covered by
            instance licenses.
        workload (list[InstanceLicenseWorkloadModel] | Unset): Array of protected workloads.
        package (ELicensePackageType | Unset): License package.
        promo_instances_number (float | Unset): Number of Promo instance licenses.
        licensed_instances_promo_included_number (float | Unset): Number of licensed instances, including Promo instance
            licenses.
        promo_expires_on (datetime.datetime | Unset): Expiration date for the Promo instance licenses.
    """

    licensed_instances_number: float
    used_instances_number: float
    new_instances_number: float
    rental_instances_number: float
    objects: list[InstanceLicenseObjectModel] | Unset = UNSET
    workload: list[InstanceLicenseWorkloadModel] | Unset = UNSET
    package: ELicensePackageType | Unset = UNSET
    promo_instances_number: float | Unset = UNSET
    licensed_instances_promo_included_number: float | Unset = UNSET
    promo_expires_on: datetime.datetime | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        licensed_instances_number = self.licensed_instances_number

        used_instances_number = self.used_instances_number

        new_instances_number = self.new_instances_number

        rental_instances_number = self.rental_instances_number

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

        package: str | Unset = UNSET
        if not isinstance(self.package, Unset):
            package = self.package.value

        promo_instances_number = self.promo_instances_number

        licensed_instances_promo_included_number = self.licensed_instances_promo_included_number

        promo_expires_on: str | Unset = UNSET
        if not isinstance(self.promo_expires_on, Unset):
            promo_expires_on = self.promo_expires_on.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "licensedInstancesNumber": licensed_instances_number,
                "usedInstancesNumber": used_instances_number,
                "newInstancesNumber": new_instances_number,
                "rentalInstancesNumber": rental_instances_number,
            }
        )
        if objects is not UNSET:
            field_dict["objects"] = objects
        if workload is not UNSET:
            field_dict["workload"] = workload
        if package is not UNSET:
            field_dict["package"] = package
        if promo_instances_number is not UNSET:
            field_dict["promoInstancesNumber"] = promo_instances_number
        if licensed_instances_promo_included_number is not UNSET:
            field_dict["licensedInstancesPromoIncludedNumber"] = licensed_instances_promo_included_number
        if promo_expires_on is not UNSET:
            field_dict["promoExpiresOn"] = promo_expires_on

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.instance_license_object_model import InstanceLicenseObjectModel
        from ..models.instance_license_workload_model import InstanceLicenseWorkloadModel

        d = dict(src_dict)
        licensed_instances_number = d.pop("licensedInstancesNumber")

        used_instances_number = d.pop("usedInstancesNumber")

        new_instances_number = d.pop("newInstancesNumber")

        rental_instances_number = d.pop("rentalInstancesNumber")

        _objects = d.pop("objects", UNSET)
        objects: list[InstanceLicenseObjectModel] | Unset = UNSET
        if _objects is not UNSET:
            objects = []
            for objects_item_data in _objects:
                objects_item = InstanceLicenseObjectModel.from_dict(objects_item_data)

                objects.append(objects_item)

        _workload = d.pop("workload", UNSET)
        workload: list[InstanceLicenseWorkloadModel] | Unset = UNSET
        if _workload is not UNSET:
            workload = []
            for workload_item_data in _workload:
                workload_item = InstanceLicenseWorkloadModel.from_dict(workload_item_data)

                workload.append(workload_item)

        _package = d.pop("package", UNSET)
        package: ELicensePackageType | Unset
        if isinstance(_package, Unset):
            package = UNSET
        else:
            package = ELicensePackageType(_package)

        promo_instances_number = d.pop("promoInstancesNumber", UNSET)

        licensed_instances_promo_included_number = d.pop("licensedInstancesPromoIncludedNumber", UNSET)

        _promo_expires_on = d.pop("promoExpiresOn", UNSET)
        promo_expires_on: datetime.datetime | Unset
        if isinstance(_promo_expires_on, Unset):
            promo_expires_on = UNSET
        else:
            promo_expires_on = isoparse(_promo_expires_on)

        instance_license_summary_model = cls(
            licensed_instances_number=licensed_instances_number,
            used_instances_number=used_instances_number,
            new_instances_number=new_instances_number,
            rental_instances_number=rental_instances_number,
            objects=objects,
            workload=workload,
            package=package,
            promo_instances_number=promo_instances_number,
            licensed_instances_promo_included_number=licensed_instances_promo_included_number,
            promo_expires_on=promo_expires_on,
        )

        instance_license_summary_model.additional_properties = d
        return instance_license_summary_model

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
