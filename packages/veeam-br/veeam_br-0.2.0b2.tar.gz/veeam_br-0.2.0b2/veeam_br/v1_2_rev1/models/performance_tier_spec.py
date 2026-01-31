from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.performance_extent_spec import PerformanceExtentSpec
    from ..models.performance_tier_advanced_settings_model import PerformanceTierAdvancedSettingsModel


T = TypeVar("T", bound="PerformanceTierSpec")


@_attrs_define
class PerformanceTierSpec:
    """Performance tier.

    Attributes:
        performance_extents (list[PerformanceExtentSpec]): Array of performance extents.
        advanced_settings (PerformanceTierAdvancedSettingsModel | Unset): Advanced settings of the performance tier.
    """

    performance_extents: list[PerformanceExtentSpec]
    advanced_settings: PerformanceTierAdvancedSettingsModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        performance_extents = []
        for performance_extents_item_data in self.performance_extents:
            performance_extents_item = performance_extents_item_data.to_dict()
            performance_extents.append(performance_extents_item)

        advanced_settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.advanced_settings, Unset):
            advanced_settings = self.advanced_settings.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "performanceExtents": performance_extents,
            }
        )
        if advanced_settings is not UNSET:
            field_dict["advancedSettings"] = advanced_settings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.performance_extent_spec import PerformanceExtentSpec
        from ..models.performance_tier_advanced_settings_model import PerformanceTierAdvancedSettingsModel

        d = dict(src_dict)
        performance_extents = []
        _performance_extents = d.pop("performanceExtents")
        for performance_extents_item_data in _performance_extents:
            performance_extents_item = PerformanceExtentSpec.from_dict(performance_extents_item_data)

            performance_extents.append(performance_extents_item)

        _advanced_settings = d.pop("advancedSettings", UNSET)
        advanced_settings: PerformanceTierAdvancedSettingsModel | Unset
        if isinstance(_advanced_settings, Unset):
            advanced_settings = UNSET
        else:
            advanced_settings = PerformanceTierAdvancedSettingsModel.from_dict(_advanced_settings)

        performance_tier_spec = cls(
            performance_extents=performance_extents,
            advanced_settings=advanced_settings,
        )

        performance_tier_spec.additional_properties = d
        return performance_tier_spec

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
