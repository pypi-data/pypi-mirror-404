from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_backup_copy_restore_points import EBackupCopyRestorePoints
from ..types import UNSET, Unset

T = TypeVar("T", bound="JobStartSpec")


@_attrs_define
class JobStartSpec:
    """Job start settings.

    Attributes:
        perform_active_full (bool): If `true`, Veeam Backup & Replication will perform an active full backup. Default:
            False.
        start_chained_jobs (bool | Unset): If `true`, Veeam Backup & Replication will start chained jobs as well.
            Default: False.
        sync_restore_points (EBackupCopyRestorePoints | Unset): Restore point type for syncing backup copy jobs with the
            immediate copy mode.
    """

    perform_active_full: bool = False
    start_chained_jobs: bool | Unset = False
    sync_restore_points: EBackupCopyRestorePoints | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        perform_active_full = self.perform_active_full

        start_chained_jobs = self.start_chained_jobs

        sync_restore_points: str | Unset = UNSET
        if not isinstance(self.sync_restore_points, Unset):
            sync_restore_points = self.sync_restore_points.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "performActiveFull": perform_active_full,
            }
        )
        if start_chained_jobs is not UNSET:
            field_dict["startChainedJobs"] = start_chained_jobs
        if sync_restore_points is not UNSET:
            field_dict["syncRestorePoints"] = sync_restore_points

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        perform_active_full = d.pop("performActiveFull")

        start_chained_jobs = d.pop("startChainedJobs", UNSET)

        _sync_restore_points = d.pop("syncRestorePoints", UNSET)
        sync_restore_points: EBackupCopyRestorePoints | Unset
        if isinstance(_sync_restore_points, Unset):
            sync_restore_points = UNSET
        else:
            sync_restore_points = EBackupCopyRestorePoints(_sync_restore_points)

        job_start_spec = cls(
            perform_active_full=perform_active_full,
            start_chained_jobs=start_chained_jobs,
            sync_restore_points=sync_restore_points,
        )

        job_start_spec.additional_properties = d
        return job_start_spec

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
