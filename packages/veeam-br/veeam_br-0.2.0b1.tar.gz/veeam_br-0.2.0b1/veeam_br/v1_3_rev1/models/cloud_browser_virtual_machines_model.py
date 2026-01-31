from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_protection_group_cloud_account_type import EProtectionGroupCloudAccountType

T = TypeVar("T", bound="CloudBrowserVirtualMachinesModel")


@_attrs_define
class CloudBrowserVirtualMachinesModel:
    """Cloud virtual machines.

    Attributes:
        service_type (EProtectionGroupCloudAccountType): Cloud account type.
    """

    service_type: EProtectionGroupCloudAccountType
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        service_type = self.service_type.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "serviceType": service_type,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        service_type = EProtectionGroupCloudAccountType(d.pop("serviceType"))

        cloud_browser_virtual_machines_model = cls(
            service_type=service_type,
        )

        cloud_browser_virtual_machines_model.additional_properties = d
        return cloud_browser_virtual_machines_model

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
