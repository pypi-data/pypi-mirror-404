from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="VSphereChangedBlockTrackingSettingsModel")


@_attrs_define
class VSphereChangedBlockTrackingSettingsModel:
    """Changed block tracking (CBT) settings for the job.

    Attributes:
        is_enabled (bool): If `true`, CBT data is used.
        enable_cb_tautomatically (bool | Unset): If `true`, CBT is enabled for all processed VMs even if CBT is disabled
            in VM configuration. CBT is used for VMs with virtual hardware version 7 or later. These VMs must not have
            existing snapshots.
        reset_cb_ton_active_full (bool | Unset): If `true`, CBT is reset before creating active full backups.
    """

    is_enabled: bool
    enable_cb_tautomatically: bool | Unset = UNSET
    reset_cb_ton_active_full: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        is_enabled = self.is_enabled

        enable_cb_tautomatically = self.enable_cb_tautomatically

        reset_cb_ton_active_full = self.reset_cb_ton_active_full

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "isEnabled": is_enabled,
            }
        )
        if enable_cb_tautomatically is not UNSET:
            field_dict["enableCBTautomatically"] = enable_cb_tautomatically
        if reset_cb_ton_active_full is not UNSET:
            field_dict["resetCBTonActiveFull"] = reset_cb_ton_active_full

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        is_enabled = d.pop("isEnabled")

        enable_cb_tautomatically = d.pop("enableCBTautomatically", UNSET)

        reset_cb_ton_active_full = d.pop("resetCBTonActiveFull", UNSET)

        v_sphere_changed_block_tracking_settings_model = cls(
            is_enabled=is_enabled,
            enable_cb_tautomatically=enable_cb_tautomatically,
            reset_cb_ton_active_full=reset_cb_ton_active_full,
        )

        v_sphere_changed_block_tracking_settings_model.additional_properties = d
        return v_sphere_changed_block_tracking_settings_model

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
