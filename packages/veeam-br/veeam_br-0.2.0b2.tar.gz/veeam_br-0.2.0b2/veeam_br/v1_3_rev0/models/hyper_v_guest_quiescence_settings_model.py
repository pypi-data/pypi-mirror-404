from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="HyperVGuestQuiescenceSettingsModel")


@_attrs_define
class HyperVGuestQuiescenceSettingsModel:
    """Microsoft Hyper-V guest quiescence settings.

    Attributes:
        is_enabled (bool): If `true`, Microsoft Hyper-V guest quiescence is used.
        crash_consistent_backup (bool | Unset): If `true`, Veeam Backup & Replication will create a crash-consistent
            backup of a VM.
    """

    is_enabled: bool
    crash_consistent_backup: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        is_enabled = self.is_enabled

        crash_consistent_backup = self.crash_consistent_backup

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "isEnabled": is_enabled,
            }
        )
        if crash_consistent_backup is not UNSET:
            field_dict["crashConsistentBackup"] = crash_consistent_backup

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        is_enabled = d.pop("isEnabled")

        crash_consistent_backup = d.pop("crashConsistentBackup", UNSET)

        hyper_v_guest_quiescence_settings_model = cls(
            is_enabled=is_enabled,
            crash_consistent_backup=crash_consistent_backup,
        )

        hyper_v_guest_quiescence_settings_model.additional_properties = d
        return hyper_v_guest_quiescence_settings_model

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
