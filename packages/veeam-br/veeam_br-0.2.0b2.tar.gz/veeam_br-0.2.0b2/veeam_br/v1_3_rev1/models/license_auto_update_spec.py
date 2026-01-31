from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="LicenseAutoUpdateSpec")


@_attrs_define
class LicenseAutoUpdateSpec:
    """Update the license automatically.

    Attributes:
        enabled (bool): If `true`, the license is automatically updated.
        proactive_support_enabled (bool | Unset): If `true`, proactive support is enabled. This option periodically
            shares anonymized, non-sensitive backup infrastructure details with Veeam.
    """

    enabled: bool
    proactive_support_enabled: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        enabled = self.enabled

        proactive_support_enabled = self.proactive_support_enabled

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "enabled": enabled,
            }
        )
        if proactive_support_enabled is not UNSET:
            field_dict["proactiveSupportEnabled"] = proactive_support_enabled

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        enabled = d.pop("enabled")

        proactive_support_enabled = d.pop("proactiveSupportEnabled", UNSET)

        license_auto_update_spec = cls(
            enabled=enabled,
            proactive_support_enabled=proactive_support_enabled,
        )

        license_auto_update_spec.additional_properties = d
        return license_auto_update_spec

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
