from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="PrimaryStorageIntegrationSettingsModel")


@_attrs_define
class PrimaryStorageIntegrationSettingsModel:
    """Primary storage integration settings for the job.

    Attributes:
        is_enabled (bool): If `true`, the primary storage integration is enabled. In this case, storage snapshots
            (instead of VM snapshots) are used for VM data processing.
        processed_vms_limit_enabled (bool | Unset): If `true`, the number of processed VMs per storage snapshot is
            limited.
        processed_vms_count (int | Unset): Number of processed VMs per storage snapshot.
        failover_to_standard_backup (bool | Unset): If `true`, failover to the regular VM processing mode is enabled. In
            this case, if backup from storage snapshot fails, VM snapshots are used.
    """

    is_enabled: bool
    processed_vms_limit_enabled: bool | Unset = UNSET
    processed_vms_count: int | Unset = UNSET
    failover_to_standard_backup: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        is_enabled = self.is_enabled

        processed_vms_limit_enabled = self.processed_vms_limit_enabled

        processed_vms_count = self.processed_vms_count

        failover_to_standard_backup = self.failover_to_standard_backup

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "isEnabled": is_enabled,
            }
        )
        if processed_vms_limit_enabled is not UNSET:
            field_dict["processedVmsLimitEnabled"] = processed_vms_limit_enabled
        if processed_vms_count is not UNSET:
            field_dict["processedVmsCount"] = processed_vms_count
        if failover_to_standard_backup is not UNSET:
            field_dict["failoverToStandardBackup"] = failover_to_standard_backup

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        is_enabled = d.pop("isEnabled")

        processed_vms_limit_enabled = d.pop("processedVmsLimitEnabled", UNSET)

        processed_vms_count = d.pop("processedVmsCount", UNSET)

        failover_to_standard_backup = d.pop("failoverToStandardBackup", UNSET)

        primary_storage_integration_settings_model = cls(
            is_enabled=is_enabled,
            processed_vms_limit_enabled=processed_vms_limit_enabled,
            processed_vms_count=processed_vms_count,
            failover_to_standard_backup=failover_to_standard_backup,
        )

        primary_storage_integration_settings_model.additional_properties = d
        return primary_storage_integration_settings_model

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
