from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_job_type import EJobType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.backup_schedule_model import BackupScheduleModel
    from ..models.entra_id_audit_log_backup_job_storage_model import EntraIDAuditLogBackupJobStorageModel
    from ..models.entra_id_audit_log_backup_job_tenant_model import EntraIDAuditLogBackupJobTenantModel


T = TypeVar("T", bound="EntraIDAuditLogBackupJobSpec")


@_attrs_define
class EntraIDAuditLogBackupJobSpec:
    """Backup job settings for Microsoft Entra ID audit logs.

    Attributes:
        name (str): Name of the job.
        type_ (EJobType): Type of the job.
        description (str): Description of the job.
        tenant (EntraIDAuditLogBackupJobTenantModel): Microsoft Entra ID tenant settings.
        is_high_priority (bool | Unset): If `true`, the resource scheduler prioritizes this job over other similar jobs
            and allocates resources to it first.
        storage (EntraIDAuditLogBackupJobStorageModel | Unset): Storage settings.
        schedule (BackupScheduleModel | Unset): Job scheduling options.
    """

    name: str
    type_: EJobType
    description: str
    tenant: EntraIDAuditLogBackupJobTenantModel
    is_high_priority: bool | Unset = UNSET
    storage: EntraIDAuditLogBackupJobStorageModel | Unset = UNSET
    schedule: BackupScheduleModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        type_ = self.type_.value

        description = self.description

        tenant = self.tenant.to_dict()

        is_high_priority = self.is_high_priority

        storage: dict[str, Any] | Unset = UNSET
        if not isinstance(self.storage, Unset):
            storage = self.storage.to_dict()

        schedule: dict[str, Any] | Unset = UNSET
        if not isinstance(self.schedule, Unset):
            schedule = self.schedule.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "type": type_,
                "description": description,
                "tenant": tenant,
            }
        )
        if is_high_priority is not UNSET:
            field_dict["isHighPriority"] = is_high_priority
        if storage is not UNSET:
            field_dict["storage"] = storage
        if schedule is not UNSET:
            field_dict["schedule"] = schedule

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.backup_schedule_model import BackupScheduleModel
        from ..models.entra_id_audit_log_backup_job_storage_model import EntraIDAuditLogBackupJobStorageModel
        from ..models.entra_id_audit_log_backup_job_tenant_model import EntraIDAuditLogBackupJobTenantModel

        d = dict(src_dict)
        name = d.pop("name")

        type_ = EJobType(d.pop("type"))

        description = d.pop("description")

        tenant = EntraIDAuditLogBackupJobTenantModel.from_dict(d.pop("tenant"))

        is_high_priority = d.pop("isHighPriority", UNSET)

        _storage = d.pop("storage", UNSET)
        storage: EntraIDAuditLogBackupJobStorageModel | Unset
        if isinstance(_storage, Unset):
            storage = UNSET
        else:
            storage = EntraIDAuditLogBackupJobStorageModel.from_dict(_storage)

        _schedule = d.pop("schedule", UNSET)
        schedule: BackupScheduleModel | Unset
        if isinstance(_schedule, Unset):
            schedule = UNSET
        else:
            schedule = BackupScheduleModel.from_dict(_schedule)

        entra_id_audit_log_backup_job_spec = cls(
            name=name,
            type_=type_,
            description=description,
            tenant=tenant,
            is_high_priority=is_high_priority,
            storage=storage,
            schedule=schedule,
        )

        entra_id_audit_log_backup_job_spec.additional_properties = d
        return entra_id_audit_log_backup_job_spec

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
