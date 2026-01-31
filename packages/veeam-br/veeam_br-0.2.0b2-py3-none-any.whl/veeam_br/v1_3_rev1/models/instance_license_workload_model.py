from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_license_platform_type import ELicensePlatformType
from ..types import UNSET, Unset

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
        platform_type (ELicensePlatformType): License platform type.
        can_be_revoked (bool): If `true`, the instance license can be revoked.
        display_name (str | Unset): Protected workload display name.
    """

    name: str
    host_name: str
    used_instances_number: float
    type_: str
    instance_id: UUID
    platform_type: ELicensePlatformType
    can_be_revoked: bool
    display_name: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        host_name = self.host_name

        used_instances_number = self.used_instances_number

        type_ = self.type_

        instance_id = str(self.instance_id)

        platform_type = self.platform_type.value

        can_be_revoked = self.can_be_revoked

        display_name = self.display_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "hostName": host_name,
                "usedInstancesNumber": used_instances_number,
                "type": type_,
                "instanceId": instance_id,
                "platformType": platform_type,
                "canBeRevoked": can_be_revoked,
            }
        )
        if display_name is not UNSET:
            field_dict["displayName"] = display_name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        host_name = d.pop("hostName")

        used_instances_number = d.pop("usedInstancesNumber")

        type_ = d.pop("type")

        instance_id = UUID(d.pop("instanceId"))

        platform_type = ELicensePlatformType(d.pop("platformType"))

        can_be_revoked = d.pop("canBeRevoked")

        display_name = d.pop("displayName", UNSET)

        instance_license_workload_model = cls(
            name=name,
            host_name=host_name,
            used_instances_number=used_instances_number,
            type_=type_,
            instance_id=instance_id,
            platform_type=platform_type,
            can_be_revoked=can_be_revoked,
            display_name=display_name,
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
