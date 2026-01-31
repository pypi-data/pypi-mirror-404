from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.e_azure_instant_vm_recovery_switchover_type import EAzureInstantVMRecoverySwitchoverType
from ..types import UNSET, Unset

T = TypeVar("T", bound="AzureInstantVMRecoverySwitchoverSettingsModel")


@_attrs_define
class AzureInstantVMRecoverySwitchoverSettingsModel:
    """Switchover settings for Instant Recovery to Azure.

    Attributes:
        type_ (EAzureInstantVMRecoverySwitchoverType): Switchover type.
        schedule_time (datetime.datetime | Unset): Date and time when switchover will be triggered.
        verify_vm_boot (bool | Unset): If `true`, Veeam Backup & Replication will verify whether the restored VM has
            booted properly.
        power_on_vm (bool | Unset): If `true`, Veeam Backup & Replication will power on the VM.
    """

    type_: EAzureInstantVMRecoverySwitchoverType
    schedule_time: datetime.datetime | Unset = UNSET
    verify_vm_boot: bool | Unset = UNSET
    power_on_vm: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        schedule_time: str | Unset = UNSET
        if not isinstance(self.schedule_time, Unset):
            schedule_time = self.schedule_time.isoformat()

        verify_vm_boot = self.verify_vm_boot

        power_on_vm = self.power_on_vm

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
            }
        )
        if schedule_time is not UNSET:
            field_dict["scheduleTime"] = schedule_time
        if verify_vm_boot is not UNSET:
            field_dict["verifyVMBoot"] = verify_vm_boot
        if power_on_vm is not UNSET:
            field_dict["powerOnVM"] = power_on_vm

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        type_ = EAzureInstantVMRecoverySwitchoverType(d.pop("type"))

        _schedule_time = d.pop("scheduleTime", UNSET)
        schedule_time: datetime.datetime | Unset
        if isinstance(_schedule_time, Unset):
            schedule_time = UNSET
        else:
            schedule_time = isoparse(_schedule_time)

        verify_vm_boot = d.pop("verifyVMBoot", UNSET)

        power_on_vm = d.pop("powerOnVM", UNSET)

        azure_instant_vm_recovery_switchover_settings_model = cls(
            type_=type_,
            schedule_time=schedule_time,
            verify_vm_boot=verify_vm_boot,
            power_on_vm=power_on_vm,
        )

        azure_instant_vm_recovery_switchover_settings_model.additional_properties = d
        return azure_instant_vm_recovery_switchover_settings_model

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
