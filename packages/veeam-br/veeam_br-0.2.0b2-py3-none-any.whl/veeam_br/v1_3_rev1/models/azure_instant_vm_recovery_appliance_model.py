from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AzureInstantVMRecoveryApplianceModel")


@_attrs_define
class AzureInstantVMRecoveryApplianceModel:
    """Helper appliance for Instant Recovery to Microsoft Azure.

    Attributes:
        subnet (str): Microsoft Azure virtual subnet for the Instant Recovery helper appliance. Make sure that the
            appliance subnet is different than the one you specify for the production VM.
        storage_account (str | Unset): Name of the Microsoft Azure storage account whose resources are used to store the
            helper appliance.
    """

    subnet: str
    storage_account: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        subnet = self.subnet

        storage_account = self.storage_account

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "subnet": subnet,
            }
        )
        if storage_account is not UNSET:
            field_dict["storageAccount"] = storage_account

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        subnet = d.pop("subnet")

        storage_account = d.pop("storageAccount", UNSET)

        azure_instant_vm_recovery_appliance_model = cls(
            subnet=subnet,
            storage_account=storage_account,
        )

        azure_instant_vm_recovery_appliance_model.additional_properties = d
        return azure_instant_vm_recovery_appliance_model

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
