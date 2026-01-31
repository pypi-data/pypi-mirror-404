from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="HealthCheckRepairOptions")


@_attrs_define
class HealthCheckRepairOptions:
    """Settings for repair of unstructured data backup or backup job.

    Attributes:
        remove_non_repairable_data_if_needed (bool | Unset): If `true`, data that cannot be repaired will be removed.
        restore_primary_from_archive_if_needed (bool | Unset): If `true`, Veeam Backup & Replication will repair the
            primary data by restoring data from the archive.
        restore_archive_from_primary_if_needed (bool | Unset): If `true`, Veeam Backup & Replication will repair the
            archive data by restoring data from the primary backup.
    """

    remove_non_repairable_data_if_needed: bool | Unset = UNSET
    restore_primary_from_archive_if_needed: bool | Unset = UNSET
    restore_archive_from_primary_if_needed: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        remove_non_repairable_data_if_needed = self.remove_non_repairable_data_if_needed

        restore_primary_from_archive_if_needed = self.restore_primary_from_archive_if_needed

        restore_archive_from_primary_if_needed = self.restore_archive_from_primary_if_needed

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if remove_non_repairable_data_if_needed is not UNSET:
            field_dict["removeNonRepairableDataIfNeeded"] = remove_non_repairable_data_if_needed
        if restore_primary_from_archive_if_needed is not UNSET:
            field_dict["restorePrimaryFromArchiveIfNeeded"] = restore_primary_from_archive_if_needed
        if restore_archive_from_primary_if_needed is not UNSET:
            field_dict["restoreArchiveFromPrimaryIfNeeded"] = restore_archive_from_primary_if_needed

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        remove_non_repairable_data_if_needed = d.pop("removeNonRepairableDataIfNeeded", UNSET)

        restore_primary_from_archive_if_needed = d.pop("restorePrimaryFromArchiveIfNeeded", UNSET)

        restore_archive_from_primary_if_needed = d.pop("restoreArchiveFromPrimaryIfNeeded", UNSET)

        health_check_repair_options = cls(
            remove_non_repairable_data_if_needed=remove_non_repairable_data_if_needed,
            restore_primary_from_archive_if_needed=restore_primary_from_archive_if_needed,
            restore_archive_from_primary_if_needed=restore_archive_from_primary_if_needed,
        )

        health_check_repair_options.additional_properties = d
        return health_check_repair_options

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
