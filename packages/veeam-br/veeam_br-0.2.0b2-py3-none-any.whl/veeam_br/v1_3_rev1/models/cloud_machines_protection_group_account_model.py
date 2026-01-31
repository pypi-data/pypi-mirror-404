from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_protection_group_cloud_account_type import EProtectionGroupCloudAccountType

T = TypeVar("T", bound="CloudMachinesProtectionGroupAccountModel")


@_attrs_define
class CloudMachinesProtectionGroupAccountModel:
    """Account settings for cloud objects.

    Attributes:
        account_type (EProtectionGroupCloudAccountType): Cloud account type.
    """

    account_type: EProtectionGroupCloudAccountType
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        account_type = self.account_type.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "accountType": account_type,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        account_type = EProtectionGroupCloudAccountType(d.pop("accountType"))

        cloud_machines_protection_group_account_model = cls(
            account_type=account_type,
        )

        cloud_machines_protection_group_account_model.additional_properties = d
        return cloud_machines_protection_group_account_model

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
