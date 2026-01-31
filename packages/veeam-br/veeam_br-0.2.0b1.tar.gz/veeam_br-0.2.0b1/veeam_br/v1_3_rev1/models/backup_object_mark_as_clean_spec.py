from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="BackupObjectMarkAsCleanSpec")


@_attrs_define
class BackupObjectMarkAsCleanSpec:
    """Information on backup objects to be marked as clean.

    Attributes:
        object_ids (list[UUID]): Array of backup object IDs to be marked as clean.
        reason (str): Reason why the backup objects are marked as clean.
        mark_restore_points_as_clean (bool | Unset): If `true`, marks all previous restore points as clean and all
            previous suspicious/infected events as false positives.
        exclude_from_detection (bool | Unset): If `true`, excludes the objects from the further scanning process.
        note_for_exclusion (str | Unset): Note for exclusion from detection.
    """

    object_ids: list[UUID]
    reason: str
    mark_restore_points_as_clean: bool | Unset = UNSET
    exclude_from_detection: bool | Unset = UNSET
    note_for_exclusion: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        object_ids = []
        for object_ids_item_data in self.object_ids:
            object_ids_item = str(object_ids_item_data)
            object_ids.append(object_ids_item)

        reason = self.reason

        mark_restore_points_as_clean = self.mark_restore_points_as_clean

        exclude_from_detection = self.exclude_from_detection

        note_for_exclusion = self.note_for_exclusion

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "objectIds": object_ids,
                "reason": reason,
            }
        )
        if mark_restore_points_as_clean is not UNSET:
            field_dict["markRestorePointsAsClean"] = mark_restore_points_as_clean
        if exclude_from_detection is not UNSET:
            field_dict["excludeFromDetection"] = exclude_from_detection
        if note_for_exclusion is not UNSET:
            field_dict["noteForExclusion"] = note_for_exclusion

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        object_ids = []
        _object_ids = d.pop("objectIds")
        for object_ids_item_data in _object_ids:
            object_ids_item = UUID(object_ids_item_data)

            object_ids.append(object_ids_item)

        reason = d.pop("reason")

        mark_restore_points_as_clean = d.pop("markRestorePointsAsClean", UNSET)

        exclude_from_detection = d.pop("excludeFromDetection", UNSET)

        note_for_exclusion = d.pop("noteForExclusion", UNSET)

        backup_object_mark_as_clean_spec = cls(
            object_ids=object_ids,
            reason=reason,
            mark_restore_points_as_clean=mark_restore_points_as_clean,
            exclude_from_detection=exclude_from_detection,
            note_for_exclusion=note_for_exclusion,
        )

        backup_object_mark_as_clean_spec.additional_properties = d
        return backup_object_mark_as_clean_spec

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
