from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.health_check_repair_options import HealthCheckRepairOptions


T = TypeVar("T", bound="FileBackupHealthCheckSpec")


@_attrs_define
class FileBackupHealthCheckSpec:
    """Settings for health check of unstructured data backup or backup job.

    Attributes:
        backup_ids (list[UUID] | Unset): Array of IDs of unstructured data backups that you want to check or repair. To
            get the IDs, run the [Get All Backups](Backups#operation/GetAllBackups) request.
        job_ids (list[UUID] | Unset): Array of IDs of unstructured data backup jobs that you want to check or repair. To
            get the IDs, run the [Get All Jobs](Jobs#operation/GetAllJobs) request.
        is_repair (bool | Unset): If `true`, Veeam Backup & Replication will repair corrupted data.
        repair_options (HealthCheckRepairOptions | Unset): Settings for repair of unstructured data backup or backup
            job.
    """

    backup_ids: list[UUID] | Unset = UNSET
    job_ids: list[UUID] | Unset = UNSET
    is_repair: bool | Unset = UNSET
    repair_options: HealthCheckRepairOptions | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        backup_ids: list[str] | Unset = UNSET
        if not isinstance(self.backup_ids, Unset):
            backup_ids = []
            for backup_ids_item_data in self.backup_ids:
                backup_ids_item = str(backup_ids_item_data)
                backup_ids.append(backup_ids_item)

        job_ids: list[str] | Unset = UNSET
        if not isinstance(self.job_ids, Unset):
            job_ids = []
            for job_ids_item_data in self.job_ids:
                job_ids_item = str(job_ids_item_data)
                job_ids.append(job_ids_item)

        is_repair = self.is_repair

        repair_options: dict[str, Any] | Unset = UNSET
        if not isinstance(self.repair_options, Unset):
            repair_options = self.repair_options.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if backup_ids is not UNSET:
            field_dict["backupIds"] = backup_ids
        if job_ids is not UNSET:
            field_dict["jobIds"] = job_ids
        if is_repair is not UNSET:
            field_dict["isRepair"] = is_repair
        if repair_options is not UNSET:
            field_dict["repairOptions"] = repair_options

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.health_check_repair_options import HealthCheckRepairOptions

        d = dict(src_dict)
        _backup_ids = d.pop("backupIds", UNSET)
        backup_ids: list[UUID] | Unset = UNSET
        if _backup_ids is not UNSET:
            backup_ids = []
            for backup_ids_item_data in _backup_ids:
                backup_ids_item = UUID(backup_ids_item_data)

                backup_ids.append(backup_ids_item)

        _job_ids = d.pop("jobIds", UNSET)
        job_ids: list[UUID] | Unset = UNSET
        if _job_ids is not UNSET:
            job_ids = []
            for job_ids_item_data in _job_ids:
                job_ids_item = UUID(job_ids_item_data)

                job_ids.append(job_ids_item)

        is_repair = d.pop("isRepair", UNSET)

        _repair_options = d.pop("repairOptions", UNSET)
        repair_options: HealthCheckRepairOptions | Unset
        if isinstance(_repair_options, Unset):
            repair_options = UNSET
        else:
            repair_options = HealthCheckRepairOptions.from_dict(_repair_options)

        file_backup_health_check_spec = cls(
            backup_ids=backup_ids,
            job_ids=job_ids,
            is_repair=is_repair,
            repair_options=repair_options,
        )

        file_backup_health_check_spec.additional_properties = d
        return file_backup_health_check_spec

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
