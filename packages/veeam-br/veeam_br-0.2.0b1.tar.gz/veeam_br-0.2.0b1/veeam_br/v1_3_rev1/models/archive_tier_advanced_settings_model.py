from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ArchiveTierAdvancedSettingsModel")


@_attrs_define
class ArchiveTierAdvancedSettingsModel:
    """Advanced settings of the archive tier.

    Attributes:
        cost_optimized_archive_enabled (bool | Unset): If `true`, backups are archived as soon as the remaining
            retention time is above the minimum storage period for the repository.
        archive_deduplication_enabled (bool | Unset): If `true`, each backup is stored as a delta to the previous one.
    """

    cost_optimized_archive_enabled: bool | Unset = UNSET
    archive_deduplication_enabled: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        cost_optimized_archive_enabled = self.cost_optimized_archive_enabled

        archive_deduplication_enabled = self.archive_deduplication_enabled

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if cost_optimized_archive_enabled is not UNSET:
            field_dict["costOptimizedArchiveEnabled"] = cost_optimized_archive_enabled
        if archive_deduplication_enabled is not UNSET:
            field_dict["archiveDeduplicationEnabled"] = archive_deduplication_enabled

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        cost_optimized_archive_enabled = d.pop("costOptimizedArchiveEnabled", UNSET)

        archive_deduplication_enabled = d.pop("archiveDeduplicationEnabled", UNSET)

        archive_tier_advanced_settings_model = cls(
            cost_optimized_archive_enabled=cost_optimized_archive_enabled,
            archive_deduplication_enabled=archive_deduplication_enabled,
        )

        archive_tier_advanced_settings_model.additional_properties = d
        return archive_tier_advanced_settings_model

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
