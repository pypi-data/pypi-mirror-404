from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="VolumeSettingsModel")


@_attrs_define
class VolumeSettingsModel:
    """Settings for Microsoft Hyper-V volume.

    Attributes:
        vs_sprovider (str): VSS provider for the volume.
        max_snapshots (int): Number of snapshots that you can store simultaneously for the volume.
    """

    vs_sprovider: str
    max_snapshots: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        vs_sprovider = self.vs_sprovider

        max_snapshots = self.max_snapshots

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "VSSprovider": vs_sprovider,
                "maxSnapshots": max_snapshots,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        vs_sprovider = d.pop("VSSprovider")

        max_snapshots = d.pop("maxSnapshots")

        volume_settings_model = cls(
            vs_sprovider=vs_sprovider,
            max_snapshots=max_snapshots,
        )

        volume_settings_model.additional_properties = d
        return volume_settings_model

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
